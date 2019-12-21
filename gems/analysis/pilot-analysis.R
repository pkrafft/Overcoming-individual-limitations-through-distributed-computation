
df = read.csv('pilot-data.csv')



shifts = c(2,3)
nets = c(5,6,7,8)

n.samples = 1000

n.boots = 11
num = 0

for(i in 1:n.samples) {

      boot.df = data.frame()
      
      for(j in 1:n.boots) {

            s = sample(shifts, 1)
      	    n = sample(nets, 1)
	    sam = df[(df['Shift'] == s)&(df['Net'] == n),]
	    boot.df = rbind(boot.df, sam)
	    }

      fit = lm(Popularity ~ Total.Evidence + Last.Evidence + Net, data = boot.df)

      num = num + as.numeric(summary(fit)$coefficients[,4]['Total.Evidence'] < 0.05)
}

cat(num/n.samples)