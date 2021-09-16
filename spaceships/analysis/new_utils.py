
import pandas as pd
import numpy as np
import json

def get_data(in_dir, n_evidence):
    
    infos = pd.read_csv('../data/' + in_dir + '/info.csv')
    nodes = pd.read_csv('../data/' + in_dir + '/node.csv')
    participants = pd.read_csv('../data/' + in_dir + '/participant.csv')
    print(sum(participants['status'] == 'approved'), sum(participants['status'] != 'approved'))
    
    infos = infos[infos['time_of_death'].isnull()]

    data,fails,parts = parse_data(infos, nodes)
    print('Total participants:',len(set(data['participant'].dropna())))

    # Remove practice trials
    data = data[data['net'] > 3]
    # Subset observed successes / failures based on how many flights participants observed
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
        net_evidence[i] =  pd.DataFrame(evidence).rolling(window = i, min_periods = 1).sum().to_numpy()
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

def get_parsed_data(data, fails, parts, part_prob, in_dir):

    last_perfs = []
    last_pops = []
    pops = []
    evidences = []
    net_evidences = []
    nets = []
    game_nets = []    
    turns = []    
    probs = []
    posteriors = []

    num_turns = max(data['turn'])

    for net in sorted(set(data['net'])): # Loop through decisions
        
        raw_evidence,net_evidence,posterior = get_evidence(fails[net], part_prob)

        for t in range(num_turns+1): # Loop through generations
            if t > 1:
                last_pops += list(mean_pop)
            if t > 0:
                mean_pop = get_pop(data,net,t)
            if t > 1:
                pops += list(mean_pop)
                evidences += list(net_evidence[1][t-2])
                net_evidences += list(net_evidence[num_turns][t-2])
                nets += [net] * len(list(mean_pop))
                game_nets += [in_dir + '-' + str(net)] * len(list(mean_pop))                
                turns += [t] * len(list(mean_pop))
                probs += list(parts[net])
                posteriors += list(posterior[num_turns][t-2])

    return pd.DataFrame({'last_pops':last_pops, # Popularity at previous generation
                         'Popularity':pops, # Popularity at current generation
                         'Last Evidence':evidences, # Evidence in the previous generation
                         'Total Evidence':net_evidences, # Evidence up to the previous generation
                         'Net':nets, # Trial
                         'Game':in_dir,
                         'Game Net':game_nets,
                         'Shift':turns, # Generation
                         'probs':probs,
                         'posteriors':posteriors
                         })
            
if __name__ == "__main__":
    import doctest
    doctest.testmod()