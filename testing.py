from datamule import Portfolio

portfolio = Portfolio('tsla')

portfolio.download_submissions(ticker='TSLA',filing_date=('2024-01-01','2024-12-31'),
                              submission_type=['10-K','10-Q','10-Q/A','10-K/A','4','4/A'])