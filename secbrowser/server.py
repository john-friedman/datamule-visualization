from flask import Flask, render_template, request, redirect
import tkinter as tk
from tkinter import filedialog
import os
from datamule import Portfolio



app = Flask(__name__)

cache = {}

def process_form_list(value):
    """Convert comma-separated string to list, handling None/empty"""
    if not value or not value.strip():
        return None
    return [item.strip() for item in value.split(',') if item.strip()]


@app.route('/document/<index>')
def document_view(index):
    global cache

    cache['document'] = cache['submission']._load_document_by_index(index)
        
    return render_template('document.html', 
                            document=cache['document'])
    
       
@app.route('/submission/<accession>', methods=['GET', 'POST'])
def submission_view(accession):
    global cache

    cache['submission'] = next((sub for sub in cache['portfolio'] if sub.accession == accession), None)
    
    return render_template('submission.html', submission=cache['submission'])
    
@app.route('/xbrl')
def xbrl_view():
    global cache
    submission = cache.get('submission')
    submission.xbrl
    print(submission.xbrl)
    
    return render_template('xbrl.html', submission=submission)

@app.route('/fundamentals')
def fundamentals_view():
    global cache
    submission = cache.get('submission')  
    submission.fundamentals

    return render_template('fundamentals.html', submission=submission)

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio_view():
    global cache
    
    portfolio_path = cache['portfolio_path']
    portfolio = cache.setdefault('portfolio', Portfolio(portfolio_path))
    
    # Handle POST actions (compress, decompress, delete)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'compress':
            portfolio.compress()
        elif action == 'decompress':
            portfolio.decompress()
        elif action == 'delete':
            portfolio.delete()
            # Reset global variables
            cache = {}
            return redirect('/')
        
        return redirect('/portfolio')
        
    return render_template('portfolio.html',
        portfolio = portfolio
    )

@app.route('/download', methods=['GET', 'POST'])
def download_submissions():
    if request.method == 'POST':
        # Handle download folder browsing
        if 'browse_download_folder' in request.form:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            try:
                folder_path = filedialog.askdirectory(
                    title="Select Download Folder",
                    initialdir=os.getcwd()
                )
                
                if folder_path:
                    return render_template('index.html', download_path=folder_path)
                    
            except Exception as e:
                print(f"Error opening file dialog: {str(e)}", "error")
            finally:
                root.destroy()
        
        # Handle download submission
        elif 'download_submissions' in request.form:
            # Get form data
            download_dir = request.form.get('download_dir')
            folder_name = request.form.get('folder_name')
            
            if not download_dir or not folder_name:
                print("Download directory and portfolio name are required", "error")
                return redirect('/')
            
            # Create portfolio instance for downloading
            download_portfolio = Portfolio(os.path.join(download_dir, folder_name))
            
            # Process form parameters
            kwargs = {}
            
            # Basic filters
            kwargs['cik'] = process_form_list(request.form.get('cik'))
            kwargs['ticker'] = process_form_list(request.form.get('ticker'))
            kwargs['submission_type'] = process_form_list(request.form.get('submission_type'))
            kwargs['filing_date'] = request.form.get('filing_start_date') or None
            kwargs['document_type'] = process_form_list(request.form.get('document_type'))
            
            # Handle accession numbers
            accession_input = request.form.get('accession_numbers')
            if accession_input:
                accessions = [acc.strip() for acc in accession_input.replace('\n', ',').split(',') if acc.strip()]
                kwargs['accession_numbers'] = accessions if accessions else None
            
            # Options
            kwargs['requests_per_second'] = int(request.form.get('requests_per_second', 5))
            kwargs['keep_filtered_metadata'] = 'keep_filtered_metadata' in request.form
            kwargs['standardize_metadata'] = 'standardize_metadata' in request.form
            kwargs['skip_existing'] = 'skip_existing' in request.form
            
            # Advanced CIK filters
            kwargs['sic'] = process_form_list(request.form.get('sic'))
            kwargs['state'] = process_form_list(request.form.get('state'))
            kwargs['category'] = request.form.get('category') or None
            kwargs['industry'] = request.form.get('industry') or None
            kwargs['exchange'] = process_form_list(request.form.get('exchange'))
            kwargs['name'] = request.form.get('name') or None
            kwargs['business_city'] = process_form_list(request.form.get('business_city'))
            kwargs['business_stateOrCountry'] = process_form_list(request.form.get('business_stateOrCountry'))
            kwargs['ein'] = request.form.get('ein') or None
            kwargs['entityType'] = request.form.get('entityType') or None
            kwargs['fiscalYearEnd'] = request.form.get('fiscalYearEnd') or None
            kwargs['insiderTransactionForIssuerExists'] = request.form.get('insiderTransactionForIssuerExists') or None
            kwargs['insiderTransactionForOwnerExists'] = request.form.get('insiderTransactionForOwnerExists') or None
            kwargs['mailing_city'] = process_form_list(request.form.get('mailing_city'))
            kwargs['mailing_stateOrCountry'] = process_form_list(request.form.get('mailing_stateOrCountry'))
            kwargs['ownerOrg'] = request.form.get('ownerOrg') or None
            kwargs['phone'] = request.form.get('phone') or None
            kwargs['sicDescription'] = request.form.get('sicDescription') or None
            kwargs['stateOfIncorporationDescription'] = request.form.get('stateOfIncorporationDescription') or None
            kwargs['tickers'] = process_form_list(request.form.get('tickers'))
            
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # Start download
            download_portfolio.download_submissions(**kwargs)
            
            # Optionally set this as the current portfolio
            cache['portfolio_path'] = os.path.join(download_dir, folder_name)
            return redirect('/portfolio')
    
    # note sure i need this
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def landing_page():
    global cache
    
    if request.method == 'POST' and 'browse_folder' in request.form:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        try:
            folder_path = filedialog.askdirectory(
                title="Select Portfolio Folder",
                initialdir=os.getcwd()
            )
            
            if folder_path:
                # reset cache
                cache = {}

                # set path
                cache['portfolio_path'] = folder_path
                return redirect('/portfolio')
                
        except Exception as e:
            print(f"Error opening file dialog: {str(e)}", "error")
        finally:
            root.destroy()
    
    return render_template('index.html')

def run_server():
    app.run(debug=True)