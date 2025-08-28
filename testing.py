from datamule import Portfolio

portfolio = Portfolio('tsla')

for sub in portfolio:
    print(sub.xbrl)