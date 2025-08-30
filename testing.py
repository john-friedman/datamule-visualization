from datamule import Portfolio

portfolio = Portfolio('tsla')

for doc in portfolio.document_type('EX-31.1'):
    if doc.filing_date == "2024-04-24":

        (doc.text.tags.persons)

        (doc.data.tags.persons)