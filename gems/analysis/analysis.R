
df = read.csv('data.csv')



shifts = c(6,7,8,9,10)
nets = c(3,4)

sub.df = data.frame()

for(s in shifts) {
  n = 3 + s%%2
  sam = df[(df['Shift'] == s)&(df['Net'] == n),]
  sub.df = rbind(sub.df, sam)
}

cat('\nPreregistered Test\n')

fit = lm(Popularity ~ Total.Evidence + Last.Evidence + Game.Net, data = sub.df)

summary(fit)
confint(fit, 'Total.Evidence')

cat('\nFull Data\n')

fit = lm(Popularity ~ Total.Evidence + Last.Evidence + Game.Net, data = df)

summary(fit)
confint(fit, 'Total.Evidence') 
