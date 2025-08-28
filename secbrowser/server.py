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
        
        return f"<pre>{content}</pre>"
        
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