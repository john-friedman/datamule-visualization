from flask import Flask, render_template, request, redirect, flash, url_for
import tkinter as tk
from tkinter import filedialog
import os
import math
from datamule import Portfolio

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Store the selected portfolio path and instance
selected_portfolio_path = None
portfolio_instance = None

def get_portfolio():
    """Get or create portfolio instance"""
    global portfolio_instance, selected_portfolio_path
    
    if not selected_portfolio_path:
        return None
        
    if portfolio_instance is None or str(portfolio_instance.path) != selected_portfolio_path:
        try:
            portfolio_instance = Portfolio(selected_portfolio_path)
            return portfolio_instance
        except Exception as e:
            flash(f"Error loading portfolio: {str(e)}", "error")
            return None
    
    return portfolio_instance

def process_form_list(value):
    """Convert comma-separated string to list, handling None/empty"""
    if not value or not value.strip():
        return None
    return [item.strip() for item in value.split(',') if item.strip()]

@app.route('/submission/<accession>/document/<int:index>')
def document_view(accession, index):
   portfolio = get_portfolio()
   if not portfolio:
       return redirect('/')
   
   submission = next((sub for sub in portfolio if sub.accession == accession), None)
   if not submission:
       flash(f"Submission {accession} not found", "error")
       return redirect('/portfolio')
   
   try:
       if index >= len(submission.metadata.content['documents']):
           flash(f"Document index {index} out of range", "error")
           return redirect(f'/submission/{accession}')
           
       document = submission._load_document_by_index(index)
       
       content = document.content
       if isinstance(content, bytes):
           content = content.decode('utf-8', errors='replace')
       
       return render_template('document.html', document=document, submission=submission, content=content, index=index)
       
   except Exception as e:
       flash(f"Error loading document: {str(e)}", "error")
       return redirect(f'/submission/{accession}')
   
@app.route('/submission/<accession>', methods=['GET', 'POST'])
def submission_view(accession):
    portfolio = get_portfolio()
    if not portfolio:
        return redirect('/')
    
    submission = next((sub for sub in portfolio if sub.accession == accession), None)
    if not submission:
        flash(f"Submission {accession} not found", "error")
        return redirect('/portfolio')
    
    xbrl = None
    fundamentals = None
    
    # Handle XBRL processing
    if request.method == 'POST' and request.form.get('action') == 'xbrl':
        try:
            xbrl = submission.xbrl
            flash("XBRL data loaded successfully", "success")
        except Exception as e:
            flash(f"Error loading XBRL data: {str(e)}", "error")
    
    # Handle Fundamentals processing
    if request.method == 'POST' and request.form.get('action') == 'fundamentals':
        try:
            fundamentals = submission.fundamentals
            flash("Fundamentals data loaded successfully", "success")
        except Exception as e:
            flash(f"Error loading fundamentals data: {str(e)}", "error")
    
    return render_template('submission.html', submission=submission, xbrl=xbrl, fundamentals=fundamentals)

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio_view():
    global selected_portfolio_path
    global portfolio_instance
    
    if not selected_portfolio_path:
        return redirect('/')
    
    portfolio = get_portfolio()
    if not portfolio:
        flash("Could not load portfolio", "error")
        return redirect('/')
    
    # Handle POST actions (compress, decompress, delete)
    if request.method == 'POST':
        action = request.form.get('action')
        
        try:
            if action == 'compress':
                portfolio.compress()
                flash("Portfolio compressed successfully", "success")
            elif action == 'decompress':
                portfolio.decompress()
                flash("Portfolio decompressed successfully", "success")
            elif action == 'delete':
                portfolio.delete()
                flash("Portfolio deleted successfully", "success")
                # Reset global variables
                selected_portfolio_path = None
                portfolio_instance = None
                return redirect('/')
        except Exception as e:
            flash(f"Error performing {action}: {str(e)}", "error")
        
        return redirect('/portfolio')
    
    # Get query parameters for filtering and pagination
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'accession')
    page_size = int(request.args.get('page_size', 25))
    page = int(request.args.get('page', 1))
    
    try:
        # Load submissions if not already loaded
        if not portfolio.submissions_loaded:
            flash("Loading submissions... this may take a moment", "info")
        
        # Get all submissions
        all_submissions = list(portfolio)
        total_submissions = len(all_submissions)
        
        # Filter submissions
        filtered_submissions = all_submissions
        
        # Apply search filter
        if search:
            filtered_submissions = [
                sub for sub in filtered_submissions 
                if search.lower() in (sub.accession or '').lower()
            ]
        

        # Sort submissions
        if sort_by == 'accession':
            filtered_submissions.sort(key=lambda x: x.accession or '')
        elif sort_by == 'date':
            filtered_submissions.sort(key=lambda x: x.filing_date or '')
        
        # Pagination
        total_filtered = len(filtered_submissions)
        total_pages = math.ceil(total_filtered / page_size) if total_filtered > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_submissions = filtered_submissions[start_idx:end_idx]
        
        # Prepare submissions for template with all needed attributes
        template_submissions = []
        for sub in paginated_submissions:
            template_submissions.append({
                'accession': sub.accession,
                'filing_date': sub.filing_date,
                'document_count': len(sub.metadata.content.get('documents', []))
            })
        
        return render_template('portfolio.html',
            portfolio_path=selected_portfolio_path,
            total_submissions=total_submissions,
            submissions_loaded=portfolio.submissions_loaded,
            submissions=template_submissions,
            search=search,
            sort_by=sort_by,
            page_size=page_size,
            page=page,
            total_pages=total_pages,
        )
    
    except Exception as e:
        flash(f"Error loading portfolio data: {str(e)}", "error")
        return render_template('portfolio.html',
            portfolio_path=selected_portfolio_path,
            total_submissions=0,
            submissions_loaded=False,
            submissions=[],
            search=search,
            sort_by=sort_by,
            page_size=page_size,
            page=page,
            total_pages=1,
            submission_types=[]
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
                    flash(f"Selected download folder: {folder_path}", "success")
                    return render_template('index.html', download_path=folder_path)
                    
            except Exception as e:
                flash(f"Error opening file dialog: {str(e)}", "error")
            finally:
                root.destroy()
        
        # Handle download submission
        elif 'download_submissions' in request.form:
            try:
                # Get form data
                download_dir = request.form.get('download_dir')
                folder_name = request.form.get('folder_name')
                
                if not download_dir or not folder_name:
                    flash("Download directory and portfolio name are required", "error")
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
                flash("Starting download... This may take some time", "info")
                download_portfolio.download_submissions(**kwargs)
                flash(f"Download completed successfully to {os.path.join(download_dir, folder_name)}", "success")
                
                # Optionally set this as the current portfolio
                global selected_portfolio_path
                selected_portfolio_path = os.path.join(download_dir, folder_name)
                return redirect('/portfolio')
                
            except Exception as e:
                flash(f"Error downloading submissions: {str(e)}", "error")
    
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def landing_page():
    global selected_portfolio_path
    
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
                selected_portfolio_path = folder_path
                flash(f"Selected portfolio: {folder_path}", "success")
                return redirect('/portfolio')
                
        except Exception as e:
            flash(f"Error opening file dialog: {str(e)}", "error")
        finally:
            root.destroy()
    
    return render_template('index.html', selected_portfolio=selected_portfolio_path)

def run_server():
    app.run(debug=True)