
import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
import numpy as np
import scipy.stats as stats

import utils

import os
import sys

import particle
import social_sampling

base_out_dir = './results/' 

models = ['Social Sampling', 'Utility Maximizing']

n_iter = 500
n_examples = 3

experiment_sets = [
    [
	'd75786f7-data-2018-01-25-big-experiment',
	'18a75a2d-data-2018-03-19-big-experiment',
    ],
    [
	'6b2b35f0-rounds-10-evidence-1-bit-experiment',
    ],
    [
	'095ddcbc-rounds-10-evidence-4-big-experiment-high-prob',
    ],
    [
	'b7d0390f-rounds-10-evidence-4-population-5',
	'abf00068-rounds-10-evidence-4-population-5',
    ],
    [
	'70f80fdf-rounds-10-evidence-1-population-5',
	'd9145d2a-rounds-10-evidence-1-population-5',
    ]
]

# names = ['Large-Population-High-Evidence',
# 	 'Large-Population-Low-Evidence',
# 	 'Large-Population-High-Success',
# 	 'Small-Population-High-Evidence',
# 	 'Small-Population-Low-Evidence']

names = ['Experiment-1',
         'Experiment-2',
         'Experiment-3',
         'Experiment-4',
         'Experiment-5',
         ]



sizes = [20,20,20,5,5]
n_evidences = [4,1,4,4,1]
part_probs = [0.6, 0.6, 0.8, 0.6, 0.6]


error_matrix = {}
error_vars = {}
error_ns = {}
for model in models:
    error_matrix[model] = []
    error_vars[model] = []
    error_ns[model] = []

model_kdes = []
model_in_sample = []

concat_df = pd.DataFrame()

for exp, experiments in enumerate(experiment_sets):
    
    for model in models:
    
        if model == 'particle-filter':
            model_func = particle.run_whole
            max_rule = False
        elif model == 'particle-max':
            model_func = particle.run_whole            
            max_rule = True
        elif model == 'Social Sampling':
            model_func = social_sampling.run_whole            
            max_rule = False
        elif model == 'Utility Maximizing':
            model_func = social_sampling.run_whole                        
            max_rule = True
        else:
            assert False

        out_dir = base_out_dir + '-'.join(model.split(' ')) + '/'
        
        try:
            os.makedirs(out_dir)
        except:
            pass

        exp_name = names[exp]
        gen_size = sizes[exp]        
        n_evidence = n_evidences[exp]
        part_prob = part_probs[exp]

        print('Experiment:', exp, 'Reps:', len(experiments), 'N:', gen_size, 'J:', n_evidence, 'Theta:', part_prob, 'Model', model)

        all_df = pd.DataFrame()

        data_slopes = []
        data_intercepts = []
        data_fits = []

        for in_dir in experiments:

            #################
            ### Read Data ###
            #################

            data,fails,parts = utils.get_data(in_dir, n_evidence)
            df = utils.get_parsed_data(data, fails, parts, part_prob)

            df['Experiment'] = exp_name
            df['exp_id'] = in_dir
            df['nets'] = df['nets'].astype('str') + '-' + in_dir

            all_df = pd.concat([all_df, df])
            if model == models[0]:
                concat_df = pd.concat([concat_df, df])

            ######################
            ### Fit Regression ###
            ######################

            fit = stats.linregress(list(df['net_evidences']), list(df['final_pops']))

            data_slopes += [fit.slope]
            data_intercepts += [fit.intercept]
            data_fits += [np.mean((df['final_pops'].values - (fit.slope + df['net_evidences'].values* fit.intercept))**2)]        
            #data_fits += [fit.rvalue**2]


        all_df.index = range(len(all_df))
        df = all_df


        #################
        ### Plot Data ###
        #################

        colors = np.array(['']*len(df['probs']))
        colors[np.array(df['probs']) > 0.5] = 'blue'
        colors[np.array(df['probs']) <= 0.5] = 'red'

        plt.figure()
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        fig, ax = plt.subplots()
        plt.scatter(df['evidences'],df['final_pops'],s=50,alpha=0.5,c=colors)
        plt.xlabel('Final Turn Sufficient Stat.')
        plt.ylabel('Popularity')
        #plt.title(exp_name.replace('-',' '))
        lims = [-0.1,1.1]
        ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
        ax.set_aspect('equal')
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        plt.savefig(out_dir + exp_name + '-pop-last-evidence.jpg', bbox_inches = 'tight')
        plt.close()

        plt.figure()
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        fig, ax = plt.subplots()
        plt.scatter(df['net_evidences'],df['final_pops'],s=50,alpha=0.5,c=colors)
        plt.xlabel('Aggregate Sufficient Stat.')
        plt.ylabel('Popularity')
        #plt.title(exp_name.replace('-',' '))
        lims = [-0.1,1.1]
        ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
        ax.set_aspect('equal')
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        plt.savefig(out_dir + exp_name + '-pop-net-evidence.jpg', bbox_inches = 'tight')
        plt.close()

        plt.figure()
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        fig, ax = plt.subplots()
        plt.scatter(df['posteriors'],df['final_pops'],s=50,alpha=0.5,c=colors)
        plt.xlabel('Normative Posterior')
        plt.ylabel('Popularity')
        #plt.title(exp_name.replace('-',' '))
        lims = [-0.1,1.1]
        ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
        ax.set_aspect('equal')
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        plt.savefig(out_dir + exp_name + '-pop-post.jpg', bbox_inches = 'tight')
        plt.close()

        error = []
        error += [np.mean(np.abs(df['evidences'] - df['final_pops'])**2)]
        error += [np.mean(np.abs(df['net_evidences'] - df['final_pops'])**2)]
        error += [np.mean(np.abs(df['posteriors'] - df['final_pops'])**2)]

        error_var = []
        error_var += [np.std(np.abs(df['evidences'] - df['final_pops'])**2)]
        error_var += [np.std(np.abs(df['net_evidences'] - df['final_pops'])**2)]
        error_var += [np.std(np.abs(df['posteriors'] - df['final_pops'])**2)]    

        error_n = []
        error_n += [len(np.abs(df['evidences'] - df['final_pops'])**2)]
        error_n += [len(np.abs(df['net_evidences'] - df['final_pops'])**2)]
        error_n += [len(np.abs(df['posteriors'] - df['final_pops'])**2)]    

        error_matrix[model] += [error]
        error_vars[model] += [error_var]
        error_ns[model] += [error_n]    

        ###################
        ### Simulations ###
        ###################

        n_parts = 8*4
        n_info = n_evidence
        n_particles = gen_size
        n_rounds = 10
        base_prob = part_prob
        mutation_rate = 0.5#base_prob    

        for i in range(n_examples):

            goods, final_pops, net_evidences, posts = model_func(n_parts, n_rounds, n_info, n_particles, mutation_rate, base_prob, max_rule = max_rule)


            ################################
            ### Plot Example Simulations ###
            ################################

            plt.figure()        
            sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
            fig, ax = plt.subplots()

            colors = np.array(['']*len(goods))
            colors[np.array(goods)] = 'blue'
            colors[~np.array(goods)] = 'red'

            plt.scatter(net_evidences,final_pops,s=50,alpha=0.5,c=colors)

            plt.xlabel('All Turns Sufficient Stat.')
            plt.ylabel('Popularity')

            lims = [-0.1,1.1]
            ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
            ax.set_aspect('equal')
            ax.set_xlim(lims)
            ax.set_ylim(lims)

            plt.savefig(out_dir + exp_name + '-pop-net-evidence-sim-example-' + str(i) + '.jpg', bbox_inches = 'tight')
            plt.close()


        all_net_evidences = []
        all_final_pops = []
        all_colors = []
        slopes, intercepts, fits = [],[],[]

        for i in range(n_iter):


            if i % 10 == 0:
                print(i)

            goods, final_pops, net_evidences, posts = model_func(n_parts, n_rounds, n_info, n_particles, mutation_rate, base_prob, max_rule = max_rule)

            all_final_pops += list(final_pops)
            all_net_evidences += list(net_evidences)

            colors = np.array(['']*len(goods))
            colors[np.array(goods)] = 'blue'
            colors[~np.array(goods)] = 'red'
            all_colors += list(colors)

            ######################
            ### Fit Regression ###
            ######################

            fit = stats.linregress(net_evidences, final_pops)
            slopes += [fit.slope]
            intercepts += [fit.intercept]
            fits += [np.mean((np.array(final_pops) - (fit.slope + np.array(net_evidences) * fit.intercept))**2)]
            #fits += [fit.rvalue**2]


        ########################
        ### Assess Model Fit ###
        ########################        

        kde = stats.gaussian_kde([all_net_evidences, all_final_pops])
        kde_fits = np.log(kde.pdf(df[['net_evidences','final_pops']].values.transpose()))
        model_kdes += [[(exp+1), model, like] for like in kde_fits]

        for rep in range(len(data_intercepts)):
            
            intercept_fit = np.mean(np.array(intercepts) < data_intercepts[rep])
            intercept_fit = min(intercept_fit, 1 - intercept_fit)                                    
            slope_fit = np.mean(np.array(slopes) < data_slopes[rep])
            slope_fit = min(slope_fit, 1 - slope_fit)                        
            fit_fit = np.mean(np.array(fits) < data_fits[rep])
            fit_fit = min(fit_fit, 1 - fit_fit)            
            
            model_in_sample += [[(exp+1), model, 'Intercept', rep, intercept_fit]]
            model_in_sample += [[(exp+1), model, 'Slope', rep, slope_fit]]
            model_in_sample += [[(exp+1), model, 'Fit', rep, fit_fit]]
        
        ########################
        ### Plot Simulations ###
        ########################        
        
        plt.figure()        
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        fig, ax = plt.subplots()
        plt.scatter(all_net_evidences,all_final_pops,s=50,alpha=0.02,c=all_colors)
        plt.xlabel('All Turns Sufficient Stat.')
        plt.ylabel('Popularity')
        lims = [-0.1,1.1]
        ax.plot(lims, lims, 'k-', alpha=0.1, zorder=0)
        ax.set_aspect('equal')
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        plt.savefig(out_dir + exp_name + '-pop-net-evidence-sim.jpg', bbox_inches = 'tight')
        plt.close()

        plt.figure()
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        plt.hist(slopes)
        for s in data_slopes:
            plt.axvline(s, color = 'k', linestyle='--', label = "Value from Data", linewidth = 3)    
        #plt.xlim(-0.75, 1.75)
        plt.xlabel('Regression Slope')
        plt.ylabel('Frequency in Simulation')


        plt.savefig(out_dir + exp_name + '-sim-slope.jpg', bbox_inches = 'tight')
        plt.close()

        plt.figure()        
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        plt.hist(intercepts)
        for s in data_intercepts:
            plt.axvline(s, color = 'k', linestyle='--', label = "Value from Data", linewidth = 3)
        #plt.xlim(-0.5, 1)        
        plt.xlabel('Regression Intercept')
        plt.ylabel('Frequency in Simulation')
        plt.savefig(out_dir + exp_name + '-sim-intercept.jpg', bbox_inches = 'tight')    
        plt.close()

        plt.figure()        
        sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
        plt.hist(fits)
        for s in data_fits:
            plt.axvline(s, color = 'k', linestyle='--', label = "Value from Data", linewidth = 3)     
        #plt.xlim(-0.05, 1)
        plt.xlabel('Regression Fit')
        plt.ylabel('Frequency in Simulation')
        plt.savefig(out_dir + exp_name + '-sim-fit.jpg', bbox_inches = 'tight')        
        plt.close()


out_dir = base_out_dir

kde_df = pd.DataFrame(model_kdes)
kde_df.columns = ['Experiment', 'Model', 'Data Log Likelihood']

plt.figure()
sns.set(context = 'paper', font_scale = 2, font='serif', style = 'white',  rc={"lines.linewidth": 2.5})
sns.barplot('Experiment', 'Data Log Likelihood', 'Model', data = kde_df, estimator = sum, ci = None)
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plt.ylabel('Data Log Likelihood')
plt.savefig(out_dir + 'model-log-like.jpg', bbox_inches = 'tight')        
plt.close()

in_sample_df = pd.DataFrame(model_in_sample)
in_sample_df.columns = ['Experiment', 'Model', 'Stat', 'Rep', 'Fit']




for model in models:

    print(model, 'Summary')
    
    print(np.round(error_matrix[model],2))
    print(np.round(1.96 * np.array(error_vars[model]) / np.sqrt(np.array(error_ns[model])),2))

    m = np.round(error_matrix[model],2)
    s = np.round(1.96 * np.array(error_vars[model]) / np.sqrt(np.array(error_ns[model])),2)

    out = ''
    for i in range(len(m)):
        out += '\\thead{Experiment ' + str(i+1) + '} & '
        for j in range(len(m[i])):
            out += '$' + str(m[i][j]) + ' \\pm ' + str(s[i][j]) + '$ & '
        out = out[:-2]
        out += '\\\\ \\hline \n'

    print(out)

    print('In Sample')
    in_sample_df['Out'] = in_sample_df['Fit'] > 0.005
    print(in_sample_df[in_sample_df['Model'] == model])    

concat_df.to_csv('evidence-pops.csv')
os.system('Rscript analyze.R > tmp')
with open('tmp') as f:
    for l in f.readlines():
        print(l)
