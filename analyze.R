
d = read.csv('evidence-pops.csv')
summary(lm(d[,'popularity'] ~ d[,'evidence'] + d[,'last_evidence'] + factor(d[,'experiment'])))
#summary(lm(d[,'popularity'] ~ d[,'evidence'] + d[,'last_evidence'] + factor(d[,'game'])))
#summary(lm(d[,'popularity'] ~ d[,'evidence'] + d[,'last_evidence'] + factor(d[,'game']) + factor(d[,'experiment'])))
