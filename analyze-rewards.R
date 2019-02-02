
d = read.csv('rewards.csv')
summary(lm(d[,'adjusted'] ~ d[,'turn'] +  factor(d[,'net'])))
#summary(lm(d[,'popularity'] ~ d[,'evidence'] + d[,'last_evidence'] + factor(d[,'game'])))
#summary(lm(d[,'popularity'] ~ d[,'evidence'] + d[,'last_evidence'] + factor(d[,'game']) + factor(d[,'experiment'])))
