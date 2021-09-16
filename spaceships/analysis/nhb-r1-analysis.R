
df = read.csv('data.csv')

fit = lm(Popularity ~ Total.Evidence + Last.Evidence + factor(Experiment) + factor(Game.Net), data = df)

summary(fit)
confint(fit, 'Total.Evidence')



