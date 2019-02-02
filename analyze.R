
d = read.csv('evidence-pops.csv')
fit = lm(d[,'final_pops'] ~ d[,'net_evidences'] + d[,'evidences'] + factor(d[,'exp_id']))
summary(fit)
print(confint(fit, 'd[, "net_evidences"]', level=0.95))
