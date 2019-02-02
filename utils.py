
import pandas as pd
import numpy as np
import scipy.misc

import matplotlib.pyplot as plt
import seaborn as sns

import json

def get_data(in_dir, n_evidence):
    
    infos = pd.read_csv('./data/' + in_dir + '/info.csv')
    nodes = pd.read_csv('./data/' + in_dir + '/node.csv')
    
    infos = infos[infos['time_of_death'].isnull()]

    data,fails,parts = parse_data(infos, nodes)

    data = data[data['net'] > 3]
    fails = get_evidence_subset(fails, n_evidence)

    nets = set(data['net'])
    parts = dict(zip(nets, [parts[i] for i in nets]))
    
    return data,fails,parts

def parse_data(infos, nodes):
    """
    >>> infos = pd.DataFrame({
    ... 'origin_id':[0,1,2,3],
    ... 'contents':[
    ... '{"turn":0,"set":1,"action":[],"fails":["fail","success","fail"],"part_probs":[0.4,0.6,0.4]}',
    ... '{"turn":1,"set":1,"action":[0,1,1],"viewed_fails":["0","success","fail"],"part_probs":[0.4,0.6,0.4]}',
    ... '{"turn":0,"set":2,"action":[],"fails":["fail","success","success"],"part_probs":[0.6,0.6,0.6]}',
    ... '{"turn":1,"set":2,"action":[1,0,1],"viewed_fails":["0","success","success"],"part_probs":[0.6,0.6,0.6]}',
    ... ]
    ... })
    >>> nodes = pd.DataFrame({
    ... 'id':[0,1,2,3],
    ... 'participant_id':[np.nan,1,np.nan,2],
    ... })
    >>> data,fails,parts = parse_data(infos,nodes)
    >>> data
          action  net  participant  turn                 viewed
    0         []    1          NaN     0                     []
    1  [0, 1, 1]    1          1.0     1     [0, success, fail]
    2         []    2          NaN     0                     []
    3  [1, 0, 1]    2          2.0     1  [0, success, success]
    >>> fails
    {1: ['fail', 'success', 'fail'], 2: ['fail', 'success', 'success']}
    >>> parts
    {1: array([ 0.4,  0.6,  0.4]), 2: array([ 0.6,  0.6,  0.6])}
    """

    participants = []    
    turns = []
    nets = []
    actions = []
    viewed = []

    fails = {}
    parts = {}

    for i in range(len(infos)):

        row = infos.iloc[i]
        contents = json.JSONDecoder().decode(row['contents'])

        turns += [contents['turn']]
        nets += [contents['set']]
        actions += [contents['action']]
        try:
            viewed += [contents['viewed_fails']]
            participants += [int(nodes[nodes['id'] == row['origin_id']]['participant_id'])]
        except:
            participants += [None]
            viewed += [[]]
            fails[contents['set']] = contents['fails']

            if contents['set'] in parts:
                assert list(parts[contents['set']]) == contents['part_probs']
            else:
                parts[contents['set']] = np.array(contents['part_probs'])

    data = pd.DataFrame({'participant':participants,'turn':turns,'net':nets,'action':actions,'viewed':viewed})

    return data,fails,parts

def get_evidence(this_fails, base_prob):
    """
    >>> this_fails = np.array([
    ... [['success','success','fail','fail'],['success','fail','fail','fail']],
    ... [['fail','fail','fail','fail'],['success','fail','fail','fail']],
    ... [['success','success','fail','fail'],['success','success','success','success']],
    ... ])
    >>> ev,ne_ev,post = get_evidence(this_fails, 0.6)
    >>> ev[1]
    array([[ 2.,  1.],
           [ 0.,  1.],
           [ 2.,  4.]])
    >>> ev[2]
    array([[ 2.,  1.],
           [ 2.,  2.],
           [ 2.,  5.]])
    >>> ev[3]
    array([[ 2.,  1.],
           [ 2.,  2.],
           [ 4.,  6.]])
    >>> ne_ev[1]
    array([[ 0.5 ,  0.25],
           [ 0.  ,  0.25],
           [ 0.5 ,  1.  ]])
    >>> ne_ev[2]
    array([[ 0.5  ,  0.25 ],
           [ 0.25 ,  0.25 ],
           [ 0.25 ,  0.625]])
    >>> ne_ev[3]
    array([[ 0.5       ,  0.25      ],
           [ 0.25      ,  0.25      ],
           [ 0.33333333,  0.5       ]])
    >>> post[1]
    >>> post[2]
    >>> post[3]
    """
    
    n_evidence = len(this_fails[0][0])
    
    evidence = np.sum(np.array(np.array(this_fails) == 'success', dtype=float),2)
    
    net_evidence = {}
    norm_evidence = {}
    posteriors = {}
    for i in range(1,len(this_fails)+1):
        net_evidence[i] = pd.rolling_sum(evidence, i, 1)
        norm = get_norm(evidence, n_evidence, i)
        norm_evidence[i] = net_evidence[i] / np.array(norm, dtype = float)
        x = net_evidence[i]
        y = norm - net_evidence[i]
        posteriors[i] = base_prob**x * (1 - base_prob)**y
        posteriors[i] /= (base_prob**x * (1 - base_prob)**y + (1 - base_prob)**x * base_prob**y)
        
    return net_evidence, norm_evidence, posteriors

def get_evidence_subset(this_fails, n_evidence):
    """
    >>> this_fails = {}
    >>> this_fails['a'] = np.array([
    ... [['success','success','fail','fail'],['success','fail','fail','fail']],
    ... [['fail','fail','fail','fail'],['success','fail','fail','fail']],
    ... [['success','success','fail','fail'],['success','success','success','success']],
    ... ]) 
    >>> get_evidence_subset(this_fails, 1)['a']
    array([[['success'],
            ['success']],
    <BLANKLINE>
           [['fail'],
            ['success']],
    <BLANKLINE>
           [['success'],
            ['success']]], 
          dtype='<U7')
    """
    
    orig_fails = this_fails
    this_fails = {}
    for i in orig_fails:
        this_fails[i] = []
        for j in range(len(orig_fails[i])):
            this_fails[i] += [[]]
            for k in range(len(orig_fails[i][j])):
                this_fails[i][j] += [list(orig_fails[i][j][k][:n_evidence])]
        this_fails[i] = np.array(this_fails[i])
                
    return this_fails

def get_norm(evidence, n_evidence, window):
    """
    >>> evidence = np.array([[1,1],[1,1],[1,1]])
    >>> get_norm(evidence, 8, 1)
    array([[ 8.,  8.],
           [ 8.,  8.],
           [ 8.,  8.]])
    >>> get_norm(evidence, 8, 2)
    array([[  8.,   8.],
           [ 16.,  16.],
           [ 16.,  16.]])
    >>> get_norm(evidence, 8, 3)
    array([[  8.,   8.],
           [ 16.,  16.],
           [ 24.,  24.]])
    """
    
    n_parts = len(evidence[0])
    norm = np.ones((len(evidence),n_parts)) * window
    norm[:window] = np.transpose(np.array([range(window)]*n_parts) + 1)
    
    return norm * n_evidence

def get_pop(data, net, t):
    """
    >>> data = pd.DataFrame({
    ... 'net':[1,1,1,2],
    ... 'turn':[0,1,1,1],
    ... 'action':[[1,1],[0,1],[1,1],[1,1]],
    ... })
    >>> pop = get_pop(data,1,1)
    >>> data
       action  net  turn
    0  [1, 1]    1     0
    1  [0, 1]    1     1
    2  [1, 1]    1     1
    3  [1, 1]    2     1
    >>> pop
    array([ 0.5,  1. ])
    """

    turn_data = data.loc[(data['turn'] == t) & (data['net'] == net)]['action']
    mean_pop = np.mean(np.array([x for x in turn_data]), 0)

    return mean_pop

def get_reward(data, part_probs, net, t, verbose = False):
    """nn
    >>> 
    >>> data = pd.DataFrame({
    ... 'net':[1,1,1,2],
    ... 'turn':[2,2,2,2],
    ... 'action':[[1,1],[0,1],[1,1],[1,1]],
    ... })
    >>> parts = {1:np.array([0.6,0.4])}
    >>> get_reward(data,parts,1,2)
    """
    
    mean_pop = get_pop(data, net, t)
    
    this_probs = part_probs[net] - 0.5

    if verbose:
        print(mean_pop, this_probs)
    
    return np.mean(mean_pop * this_probs)


def get_stochastic_reward(data, fails, net, t):
    """
    >>> 
    >>> data = pd.DataFrame({
    ... 'net':[1,1,1,2],
    ... 'turn':[2,2,2,2],
    ... 'action':[[1,1],[0,1],[1,1],[1,1]],
    ... })
    >>> fails = {1:np.array([
    ... [['success','success','fail','fail'],['success','fail','fail','fail']],
    ... [['fail','fail','fail','fail'],['success','fail','fail','fail']],
    ... [['success','success','fail','fail'],['success','success','success','success']],
    ... ])}
    >>> get_stochastic_reward(data,fails,1,2)
    """

    mean_pop = get_pop(data, net, t)
    
    this_fails = fails[net]
    successes = np.sum(np.array(np.array(this_fails) == 'success', dtype=float),2)
    fails = np.sum(np.array(np.array(this_fails) == 'fail', dtype=float),2)
    totals = successes - fails    

    if t > 1:
        print(mean_pop, totals[t-2], totals[t-1])
    else:
        print(mean_pop, totals[t-1])
    
    return np.mean(mean_pop * totals[t-1])

def get_parsed_data(data, fails, parts, part_prob, verbose = False):
    
    last_perfs = []
    last_pops = []
    pops = []
    evidences = []
    net_evidences = []
    final_pops = []
    nets = []
    probs = []
    posteriors = []

    num_turns = max(data['turn'])

    for net in sorted(set(data['net'])):
        
        raw_evidence,net_evidence,posterior = get_evidence(fails[net], part_prob)

        if verbose:
            print('Net', net)
            print(net_evidence[1][:(num_turns-1)])
            print(np.array(net_evidence[num_turns][:(num_turns-1)] * 100,dtype=int)/100.0)

        for t in range(num_turns+1):

            if t > 1:
                last_perfs += list(net_evidence[num_turns][t-2])
                last_pops += list(mean_pop)

            if t > 0:
                mean_pop = get_pop(data,net,t)
                if verbose:
                    print(mean_pop)

            if t > 1:
                pops += list(mean_pop)

        for window in range(1,num_turns):
            if verbose:
                print('Final correlation with last',window,'evidence', np.corrcoef(net_evidence[window][t-2],mean_pop)[0,1])

        evidences += list(net_evidence[1][t-2])
        net_evidences += list(net_evidence[num_turns][t-2])
        final_pops += list(mean_pop)
        nets += [net] * len(list(mean_pop))
        probs += list(parts[net])
        posteriors += list(posterior[num_turns][t-2])

    return pd.DataFrame({'evidences':evidences,
                         'net_evidences':net_evidences,
                         'final_pops':final_pops,
                         'nets':nets,
                         'probs':probs,
                         'posteriors':posteriors})

def make_plot(df, out_file, size, title = None):

    colors = np.array(['']*len(df['probs']))
    colors[np.array(df['probs']) > 0.5] = 'blue'
    colors[np.array(df['probs']) <= 0.5] = 'red'

    fig, ax = plt.subplots()

    sns.set(context = 'paper', font_scale = size, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
    plt.scatter(df['net_evidences'],df['final_pops'],s=50,alpha=0.25,c=colors)
    plt.xlabel('Total Evidence')
    plt.ylabel('Popularity')
    if title is not None:
        plt.title(title)

    lims = [
            np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
                  np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
                  ]

    ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
    ax.set_aspect('equal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    plt.savefig(out_file, bbox_inches = 'tight')

    print('correlation with net evidence', np.corrcoef(df['net_evidences'],df['final_pops'])[0,1])
    print('correlation with last evidence', np.corrcoef(df['evidences'],df['final_pops'])[0,1])    

def simulate_data(data, fails, nets, stochastic):

    num_turns = max(data['turn'])
    num_agents = int(sum(data['turn'] == max(data['turn'])) / len(set(nets)))
    num_actions = 8
    actions = []

    for n in set(nets):

        for t in range(num_turns):

            this_actions = []

            for i in range(num_agents):

                action = [n,t,i,[]]

                for j in range(num_actions):

                    if t > 0:
                        viewed_fails = last_actions[np.random.choice(num_agents)]

                    if t == 0:
                        choice = np.random.random() < 0.5
                    elif not viewed_fails[j]:
                        choice = np.random.random() < 0.4
                    else:
                        
                        signal = np.mean(fails[n][t][j] == 'success')

                        if stochastic:
                            if signal == 1.0:
                                choice = np.random.random() < (base_prob**4) / (base_prob**4 + (1 - base_prob)**4)
                            elif signal == 0.75:
                                choice = np.random.random() < (base_prob**3 * (1 - base_prob)**1) / (base_prob**3 * (1 - base_prob)**1 + (1 - base_prob)**3 * base_prob**1)
                            elif signal == 0.5:
                                choice = np.random.random() < (base_prob**2 * (1 - base_prob)**2) / (base_prob**2 * (1 - base_prob)**2 + (1 - base_prob)**2 * base_prob**2)
                            elif signal == 0.25:
                                choice = np.random.random() < (base_prob**1 * (1 - base_prob)**3) / (base_prob**1 * (1 - base_prob)**3 + (1 - base_prob)**1 * base_prob**3)
                            elif signal == 0.0:
                                choice = np.random.random() < (base_prob**0 * (1 - base_prob)**4) / (base_prob**0 * (1 - base_prob)**4 + (1 - base_prob)**0 * base_prob**4)
                            else:
                                assert False
                        else:
                            choice = np.random.random() < np.round(signal)
                                
                    action[-1] += [choice]

                this_actions += [action[-1]]
                actions += [action]

            last_actions = this_actions
            
    sim_data = pd.DataFrame(actions)
    sim_data.columns = ['net','turn','agent','action']

    return sim_data
            
if __name__ == "__main__":
    import doctest
    doctest.testmod()
