from flask import Flask, render_template, request, redirect, Response, jsonify, session
import tkinter as tk
from tkinter import filedialog
import os
from datamule import Portfolio


# move to utils
def apply_highlights_to_fragment(text, highlights, fragment_id):
    """Apply highlighting to a specific text fragment"""
    fragment_matches = [h for h in highlights if h.get('fragment_id') == fragment_id]
    if not fragment_matches:
        return text
    
    fragment_matches.sort(key=lambda x: x['start'], reverse=True)
    
    highlighted_text = text
    for match in fragment_matches:
        start, end = match['start'], match['end']
        color = match['color']
        match_type = match['type']
        original = highlighted_text[start:end]
        span = f'<span style="background-color: {color}; color: white; padding: 2px; border-radius: 3px;" title="{match_type}: {original}">{original}</span>'
        highlighted_text = highlighted_text[:start] + span + highlighted_text[end:]
    
    return highlighted_text

def process_document(doc_dict, html, level, highlights=None, parent_id=''):
    """Process document elements recursively"""
    # Sort keys to ensure numerical order for items like "1", "2", etc.
    try:
        sorted_keys = sorted(doc_dict.keys(), key=lambda x: (not x.lstrip('-').isdigit(), int(x) if x.lstrip('-').isdigit() else x))
    except:
        # Fallback if sorting fails
        sorted_keys = list(doc_dict.keys())
    
    for key in sorted_keys:
        value = doc_dict[key]
        current_id = f"{parent_id}_{key}" if parent_id else key
        
        if isinstance(value, dict):
            section_title = value.get("title", "")
            
            # Output the section title with highlighting if applicable
            if section_title:
                heading_level = min(level, 6)  # Limit to h6
                if highlights:
                    highlighted_title = apply_highlights_to_fragment(section_title, highlights, 'title')
                    html.append(f'<h{heading_level}>{highlighted_title}</h{heading_level}>')
                else:
                    html.append(f'<h{heading_level}>{section_title}</h{heading_level}>')
            
            # Process the section content
            html.append('<div class="section">')
            
            # Handle direct content fields
            for attr_key, attr_value in value.items():
                if attr_key not in ["title", "class", "contents", "standardized_title"]:
                    process_content(attr_key, attr_value, html, highlights, attr_key)
            
            # Process contents dictionary if it exists
            if "contents" in value and value["contents"]:
                process_document(value["contents"], html, level + 1, highlights, current_id)
                
            html.append('</div>')
        else:
            # Direct content
            process_content(key, value, html, highlights, key)

def process_content(content_type, content, html, highlights=None, fragment_id=None):
    """Process specific content types"""
    if content_type == "text":
        if highlights and fragment_id:
            highlighted_content = apply_highlights_to_fragment(content, highlights, fragment_id)
            html.append(f'<div>{highlighted_content}</div>')
        else:
            html.append(f'<div>{content}</div>')
    elif content_type == "textsmall":
        if highlights and fragment_id:
            highlighted_content = apply_highlights_to_fragment(content, highlights, fragment_id)
            html.append(f'<div class="textsmall">{highlighted_content}</div>')
        else:
            html.append(f'<div class="textsmall">{content}</div>')
    elif content_type == "image":
        process_image(content, html)
    elif content_type == "table":
        process_table(content, html)
    else:
        pass

def process_image(image_data, html):
    """Convert image data to HTML img tag"""
    src = image_data.get('src', '')
    alt = image_data.get('alt', 'Image')
    
    html.append('<div class="image-wrapper">')
    html.append(f'<img src="{src}" alt="{alt}" class="document-image">')
    html.append('</div>')

def process_table_cell(cell):
    """Process a single table cell that may contain text or image data"""
    if isinstance(cell, dict):
        if 'image' in cell:
            # Cell contains an image
            image_data = cell['image']
            src = image_data.get('src', '')
            alt = image_data.get('alt', 'Image')
            return f'<img src="{src}" alt="{alt}" class="table-image">'
        elif 'text' in cell:
            # Cell contains structured text data
            return cell['text']
        else:
            # Cell is a dict but doesn't match expected structure
            return str(cell)
    else:
        # Cell is a string or other simple type
        return str(cell)

def process_table(table_data, html):
    """Convert table data to HTML table"""
    html.append('<table>')
    
    # Check if first row should be treated as header
    has_header = False
    if len(table_data) > 1:
        # Heuristic: if first row contains mostly text content, treat as header
        first_row = table_data[0]
        text_cells = 0
        for cell in first_row:
            if isinstance(cell, str) and cell.strip():
                text_cells += 1
            elif isinstance(cell, dict) and cell.get('text', '').strip():
                text_cells += 1
        
        if text_cells >= len(first_row) / 2:  # At least half the cells have text
            has_header = True
    
    for i, row in enumerate(table_data):
        html.append('<tr>')
        for cell in row:
            # Use th for header cells, otherwise td
            tag = 'th' if has_header and i == 0 else 'td'
            cell_content = process_table_cell(cell)
            html.append(f'<{tag}>{cell_content}</{tag}>')
        html.append('</tr>')
    
    html.append('</table>')

def visualize_data_as_html(data, highlights=None):
    data_dict = data
    html = []
    
    # Add HTML document opening tags and CSS
    html.append("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Visualization</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                line-height: 1.6; 
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .metadata-box { 
                background-color: #f8f9fa; 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin-bottom: 20px; 
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .metadata-title { 
                font-weight: bold; 
                margin-bottom: 10px; 
                font-size: 1.2em;
                color: #555;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 15px 0; 
                background-color: white;
            }
            table, th, td { 
                border: 2px solid #ddd; 
            }
            th, td { 
                padding: 10px; 
                text-align: left; 
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .textsmall { 
                font-size: 0.85em; 
                color: #666; 
            }
            .section { 
                margin-left: 20px; 
                margin-bottom: 15px; 
                padding-left: 10px;
                border-left: 1px solid #eee;
            }
            h1, h2, h3, h4, h5, h6 {
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #333;
            }
            div {
                margin: 0.5em 0;
            }
            .document-image {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin: 10px 0;
            }
            .table-image {
                max-width: 200px;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            .image-wrapper {
                text-align: center;
                margin: 15px 0;
            }
        </style>
    </head>
    <body>
    """)
    
    # Add metadata box
    if "metadata" in data_dict:
        html.append('<div class="metadata-box">')
        html.append('<div class="metadata-title">Parser Metadata</div>')
        metadata = data_dict["metadata"]
        for key, value in metadata.items():
            html.append(f'<div><strong>{key}:</strong> {value}</div>')
        html.append('</div>')
    
    # Process the document structure
    if "document" in data_dict:
        html.append('<div class="document">')
        process_document(data_dict["document"], html, 1, highlights)
        html.append('</div>')
    
    # Add HTML closing tags
    html.append("""
    </body>
    </html>
    """)
    return html
app = Flask(__name__)

cache = {}

def process_form_list(value):
    """Convert comma-separated string to list, handling None/empty"""
    if not value or not value.strip():
        return None
    return [item.strip() for item in value.split(',') if item.strip()]

@app.route('/process_tags', methods=['POST'])
def process_tags():
    global cache
    document = cache.get('document')
    
    if not document:
        return redirect('/')
    
    # Get form data
    selected_tags = request.form.getlist('tags')
    selected_similarity = request.form.getlist('similarity')
    
    # Get colors for each tag type
    colors = {}
    for tag_type in ['tickers', 'persons', 'cusips', 'isins', 'figis']:
        color_key = f'{tag_type}_color'
        if color_key in request.form:
            colors[tag_type] = request.form[color_key]
    
    # Set up dictionaries based on form selections
    from datamule.tags.config import set_dictionaries
    active_dictionaries = []
    
    # Check each dictionary type selection
    dict_mappings = {
        'persons_dict': ['ssa_baby_first_names', '8k_2024_persons'],
        'cusips_dict': ['sc13dg_cusips', '13fhr_information_table_cusips'], 
        'figis_dict': ['npx_figis'],
        'isins_dict': ['npx_isins'],
        'sentiment_dict': ['loughran_mcdonald']
    }
    
    for dict_type, dict_options in dict_mappings.items():
        selected_dict = request.form.get(dict_type)
        if selected_dict and selected_dict != 'none' and selected_dict in dict_options:
            active_dictionaries.append(selected_dict)
    
    # Also add loughran_mcdonald if similarity is selected
    if 'loughran_mcdonald' in selected_similarity:
        if 'loughran_mcdonald' not in active_dictionaries:
            active_dictionaries.append('loughran_mcdonald')
    
    # Set active dictionaries
    if active_dictionaries:
        set_dictionaries(active_dictionaries)
    else:
        set_dictionaries([])
    
    # Collect all matches with their positions and colors
    all_matches = []
    
    # Process each selected tag type
    for tag_type in selected_tags:
        color = colors.get(tag_type, "#C316C6") 
        
        if tag_type == 'tickers':
            # Tickers work differently - need to extract from the ticker object
            ticker_data = document.text.tags.tickers
            if ticker_data and hasattr(ticker_data, '_tickers_data') and ticker_data._tickers_data:
                # Get all ticker matches from the 'all' category
                ticker_matches = ticker_data._tickers_data.get('all', [])
                for match_info in ticker_matches:
                    # Ticker matches should have format (ticker, start, end)
                    if len(match_info) >= 3:
                        ticker, start, end = match_info[:3]
                        all_matches.append({
                            'match': ticker,
                            'start': start,
                            'end': end,
                            'color': color,
                            'type': 'tickers'
                        })
        
        elif tag_type == 'persons':
            persons = document.text.tags.persons
            for match, start, end in persons:
                all_matches.append({
                    'match': match,
                    'start': start,
                    'end': end,
                    'color': color,
                    'type': 'persons'
                })
        
        elif tag_type == 'cusips':
            cusips = document.text.tags.cusips
            for match, start, end in cusips:
                all_matches.append({
                    'match': match,
                    'start': start,
                    'end': end,
                    'color': color,
                    'type': 'cusips'
                })
        
        elif tag_type == 'isins':
            isins = document.text.tags.isins
            for match, start, end in isins:
                all_matches.append({
                    'match': match,
                    'start': start,
                    'end': end,
                    'color': color,
                    'type': 'isins'
                })
        
        elif tag_type == 'figis':
            figis = document.text.tags.figis
            for match, start, end in figis:
                all_matches.append({
                    'match': match,
                    'start': start,
                    'end': end,
                    'color': color,
                    'type': 'figis'
                })
    
    # Sort matches by start position (descending) to avoid position shifts when highlighting
    all_matches.sort(key=lambda x: x['start'], reverse=True)
    
    # Apply highlighting to the text
    highlighted_text = str(document.text)
    
    for match_info in all_matches:
        start = match_info['start']
        end = match_info['end']
        color = match_info['color']
        match_type = match_info['type']
        
        # Create highlighted span
        original_text = highlighted_text[start:end]
        highlighted_span = f'<span style="background-color: {color}; color: white; padding: 2px; border-radius: 3px;" title="{match_type}: {original_text}">{original_text}</span>'
        
        # Replace the text
        highlighted_text = highlighted_text[:start] + highlighted_span + highlighted_text[end:]
    
    # Convert newlines to HTML breaks for display
    highlighted_text = highlighted_text.replace('\n', '<br>')

    similarity_results = None
    if 'loughran_mcdonald' in selected_similarity:
        similarity_results = document.text.similarity.loughran_mcdonald
        print(f"sim: {similarity_results}")
    
    return render_template('text.html', 
                     document=document,
                     highlighted_text=highlighted_text,
                     matches_found=len(all_matches),
                     selected_tags=selected_tags,
                     selected_similarity=selected_similarity,
                     colors=colors,
                     form_data=request.form,
                     similarity_results=similarity_results)



@app.route('/document/<index>')
def document_view(index):
    global cache

    cache['document'] = cache['submission']._load_document_by_index(int(index))
        
    return render_template('document.html', 
                            document=cache['document'])
    
       
@app.route('/submission/<accession>', methods=['GET', 'POST'])
def submission_view(accession):
    global cache

    cache['submission'] = next((sub for sub in cache['portfolio'] if sub.accession == accession), None)
    
    return render_template('submission.html', submission=cache['submission'])

@app.route('/document/content')
def content_view():
    global cache
    document = cache.get('document')
    
    return Response(
        document.content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': 'inline',
            'X-Content-Type-Options': 'nosniff'
        }
    )

@app.route('/document/visualize', methods=['GET', 'POST'])
def visualize_view():
    global cache
    document = cache.get('document')
    
    if not document:
        return redirect('/')
    
    if request.method == 'POST':
        # Get form data
        selected_tags = request.form.getlist('tags')
        selected_similarity = request.form.getlist('similarity')
        
        # Get colors for each tag type
        colors = {}
        for tag_type in ['tickers', 'persons', 'cusips', 'isins', 'figis']:
            color_key = f'{tag_type}_color'
            if color_key in request.form:
                colors[tag_type] = request.form[color_key]
        
        # Set up dictionaries based on form selections
        from datamule.tags.config import set_dictionaries
        active_dictionaries = []
        
        # Check each dictionary type selection
        dict_mappings = {
            'persons_dict': ['ssa_baby_first_names', '8k_2024_persons'],
            'cusips_dict': ['sc13dg_cusips', '13fhr_information_table_cusips'], 
            'figis_dict': ['npx_figis'],
            'isins_dict': ['npx_isins'],
            'sentiment_dict': ['loughran_mcdonald']
        }
        
        for dict_type, dict_options in dict_mappings.items():
            selected_dict = request.form.get(dict_type)
            if selected_dict and selected_dict != 'none' and selected_dict in dict_options:
                active_dictionaries.append(selected_dict)
        
        # Also add loughran_mcdonald if similarity is selected
        if 'loughran_mcdonald' in selected_similarity:
            if 'loughran_mcdonald' not in active_dictionaries:
                active_dictionaries.append('loughran_mcdonald')
        
        # Set active dictionaries
        if active_dictionaries:
            set_dictionaries(active_dictionaries)
        else:
            set_dictionaries([])
        
        # Collect all matches with their positions and colors from document.data
        all_matches = []
        
        # Process each selected tag type using document.data.tags
        for tag_type in selected_tags:
            color = colors.get(tag_type, '#000000')
            
            if tag_type == 'tickers':
                # Tickers work differently - need to extract from the ticker object
                ticker_data = document.data.tags.tickers
                if ticker_data and hasattr(ticker_data, '_tickers_data') and ticker_data._tickers_data:
                    ticker_matches = ticker_data._tickers_data.get('all', [])
                    for match_info in ticker_matches:
                        if len(match_info) >= 3:
                            ticker, start, end = match_info[:3]
                            all_matches.append({
                                'match': ticker,
                                'fragment_id': None,
                                'start': start,
                                'end': end,
                                'color': color,
                                'type': 'tickers'
                            })
            
            elif tag_type == 'persons':
                persons = document.data.tags.persons
                for match, fragment_id, start, end in persons:
                    all_matches.append({
                        'match': match,
                        'fragment_id': fragment_id,
                        'start': start,
                        'end': end,
                        'color': color,
                        'type': 'persons'
                    })
            
            elif tag_type == 'cusips':
                cusips = document.data.tags.cusips
                for match, fragment_id, start, end in cusips:
                    all_matches.append({
                        'match': match,
                        'fragment_id': fragment_id,
                        'start': start,
                        'end': end,
                        'color': color,
                        'type': 'cusips'
                    })
            
            elif tag_type == 'isins':
                isins = document.data.tags.isins
                for match, fragment_id, start, end in isins:
                    all_matches.append({
                        'match': match,
                        'fragment_id': fragment_id,
                        'start': start,
                        'end': end,
                        'color': color,
                        'type': 'isins'
                    })
            
            elif tag_type == 'figis':
                figis = document.data.tags.figis
                for match, fragment_id, start, end in figis:
                    all_matches.append({
                        'match': match,
                        'fragment_id': fragment_id,
                        'start': start,
                        'end': end,
                        'color': color,
                        'type': 'figis'
                    })
        
        # Process similarity results
        similarity_results = None
        if 'loughran_mcdonald' in selected_similarity:
            similarity_results = document.data.similarity.loughran_mcdonald
        

        # Generate visualization HTML with highlighting
        data_visualization = '\n'.join(visualize_data_as_html(document.data, all_matches))
        
        return render_template('visualize.html', 
                             document=document,
                             data_visualization=data_visualization,
                             matches_found=len(all_matches),
                             selected_tags=selected_tags,
                             selected_similarity=selected_similarity,
                             colors=colors,
                             form_data=request.form,
                             similarity_results=similarity_results)
    
    else:
        # Default GET request - show standard visualization
        html = visualize_data_as_html(document.data)
        return render_template('visualize.html', 
                             document=document,
                             data_visualization='\n'.join(html))

@app.route('/document/data')
def data_view():
    global cache
    document = cache.get('document')
    
    return jsonify(document.data)

@app.route('/document/open')
def open_view():
    global cache
    document = cache.get('document')
    
    # Manual mapping since mimetypes is being unreliable
    ext_to_mime = {
        '.htm': 'text/html',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.txt': 'text/plain',
        '.xml': 'text/xml'
    }
    
    mime_type = ext_to_mime.get(document.extension.lower(), 'text/plain')
    
    print(f"Extension: {document.extension}")
    print(f"Mime type: {mime_type}")

    return Response(
        document.content,
        mimetype=mime_type,
        headers={
            'Content-Disposition': 'inline',
            'X-Content-Type-Options': 'nosniff'
        }
    )
@app.route('/document/text')
def text_view():
    global cache
    document = cache.get('document')
    document.text
    
    return render_template('text.html', document=document)

@app.route('/document/tables')
def tables_view():
    global cache
    document = cache.get('document')
    return render_template('tables.html', tables=document.tables)
    
@app.route('/xbrl')
def xbrl_view():
    global cache
    submission = cache.get('submission')
    submission.xbrl
    
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