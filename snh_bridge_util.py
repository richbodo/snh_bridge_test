# This Utility is a command-line tool that exercises the API of the SNH Bridge
# It is used to test the API and to ensure that it is working as expected
# It is also used to exercise the API for development purposes

import requests
import json
import argparse
import sys
import os
from pathlib import Path
from configparser import ConfigParser

BASE_URL = "https://vector-knowledge-base-RichBodo.replit.app"

def get_api_key():
    """Get API key from environment variable or config file."""
    # First, check environment variable
    api_key = os.getenv('SNH_BRIDGE_API_KEY')
    if api_key:
        return api_key

    # Next, check for config file
    config_file = os.path.expanduser('~/.snh_bridge/config.ini')
    if os.path.exists(config_file):
        config = ConfigParser()
        config.read(config_file)
        try:
            return config['auth']['api_key']
        except (KeyError, ValueError):
            pass

    return None

def setup_api_key(api_key):
    """Save API key to configuration file."""
    config_dir = os.path.expanduser('~/.snh_bridge')
    config_file = os.path.join(config_dir, 'config.ini')
    
    # Create config directory if it doesn't exist
    os.makedirs(config_dir, mode=0o700, exist_ok=True)
    
    config = ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    
    if not config.has_section('auth'):
        config.add_section('auth')
    
    config['auth']['api_key'] = api_key
    
    # Save with restricted permissions
    with open(config_file, 'w', encoding='utf-8') as f:
        os.chmod(config_file, 0o600)
        config.write(f)
    
    print(f"API key saved to {config_file}")

def get_headers(is_file_upload=False):
    """Get headers including API key as Bearer token."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "API key not found. Please either:\n"
            "1. Set SNH_BRIDGE_API_KEY environment variable, or\n"
            "2. Run: python snh_bridge_util.py configure --api-key YOUR_API_KEY"
        )
    
    print(f"Debug: API key found (length: {len(api_key)})")
    headers = {
        'Authorization': f'Bearer {api_key}'  # Use Bearer token authentication
    }
    
    # Only add Content-Type for non-file uploads
    if not is_file_upload:
        headers['Content-Type'] = 'application/json'
    
    print(f"Debug: Request headers: {headers}")
    return headers

def upload_pdf(file_path):
    """Upload a PDF file to the API."""
    print(f"\nSending POST request to: {BASE_URL}/api/upload")
    
    if not Path(file_path).exists():
        print(f"Error: File {file_path} does not exist")
        return False
        
    print(f"\nStarting upload process for: {file_path}")
    print(f"Target URL: {BASE_URL}/api/upload")
    
    try:
        print("Opening file...")
        with open(file_path, 'rb') as f:
            # Get file size for progress tracking
            file_size = Path(file_path).stat().st_size
            print(f"File size: {file_size} bytes")
            
            # Create file tuple with filename
            files = {
                'file': (os.path.basename(file_path), f, 'application/pdf')
            }
            
            # Get headers but don't set Content-Type
            headers = get_headers(is_file_upload=True)
            print(f"Debug: Request headers: {headers}")
            
            print("File opened successfully. Initiating upload request...")
            
            # Use a session to track redirects
            session = requests.Session()
            response = session.post(
                f"{BASE_URL}/api/upload",
                files=files,
                headers=headers,
                allow_redirects=False  # We'll handle redirects manually to track them
            )
            
            print(f"\nUpload completely sent off: {file_size} bytes")
            
            # Track any redirects
            history = []
            while response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers['Location']
                print(f"Received HTTP {response.status_code} redirect to: {redirect_url}")
                history.append(response)
                response = session.get(redirect_url, allow_redirects=False)
            
            if history:
                print(f"\nFollowed {len(history)} redirect(s) to final URL: {response.url}")
            
            print(f"\nFinal response status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Raw response content: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        print("\nUpload successful!")
                        print(f"Document ID: {result['document_id']}")
                        print(f"Message: {result['message']}")
                        print("\nMetadata:")
                        metadata = result.get('metadata', {})
                        print(f"Filename: {metadata.get('filename')}")
                        print(f"Size: {metadata.get('size')} bytes")
                        print(f"Content Type: {metadata.get('content_type')}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print("\nWarning: Server returned 200 but response was not valid JSON")
                    print(f"Response content type: {response.headers.get('content-type', 'not specified')}")
                    print(f"Non-JSON response content: {response.text}")
                    return False
                return True
            else:
                print(f"\nError: Upload failed with status {response.status_code}")
                try:
                    error_response = response.json()
                    print(f"Error: {error_response.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"Response content: {response.text}")
                return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nConnection Error: Could not reach server at {BASE_URL}")
        print(f"Details: {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nRequest Error: {str(e)}")
        print(f"Response content (if available): {getattr(e.response, 'text', 'No response content')}")
        return False
    except Exception as e:
        print(f"\nUnexpected Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def query_documents(query_text):
    """Query the documents using semantic search."""
    try:
        headers = get_headers()
        data = {'query': query_text}
        
        response = requests.post(f"{BASE_URL}/api/query", 
                               headers=headers,
                               json=data)
                               
        if response.status_code == 200:
            results = response.json().get('results', [])
            if not results:
                print("\nNo relevant matches found")
                return
                
            print("\nSearch Results:")
            print("--------------")
            for idx, result in enumerate(results, 1):
                print(f"\nResult {idx}:")
                print(f"Title: {result['title']}")
                print(f"Content: {result['content']}")
                print(f"Score: {result['score']:.2f}")
                metadata = result.get('metadata', {})
                print("Metadata:")
                print(f"  Source: {metadata.get('source')}")
                print(f"  File Type: {metadata.get('file_type')}")
                print(f"  Uploaded At: {metadata.get('uploaded_at')}")
                print(f"  File Size: {metadata.get('file_size')}")
        else:
            try:
                error_response = response.json()
                print(f"Error: {error_response.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                print(f"Error: Unexpected response format")
                print(f"Response content: {response.text}")
            
    except Exception as e:
        print(f"Error querying documents: {str(e)}")

def find_pdf_files(directory):
    """Recursively find all PDF files in directory and its subdirectories."""
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Store full path and relative path for better reporting
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                pdf_files.append((full_path, rel_path))
    return pdf_files

def batch_upload(directory):
    """Upload all PDF files from a directory and its subdirectories."""
    if not os.path.isdir(directory):
        print(f"\nError: {directory} is not a valid directory")
        return False
        
    pdf_files = find_pdf_files(directory)
    
    if not pdf_files:
        print(f"\nNo PDF files found in {directory} or its subdirectories")
        return False
        
    print(f"\nFound {len(pdf_files)} PDF files to upload")
    print("\nFiles to process:")
    for _, rel_path in pdf_files:
        print(f"  {rel_path}")
    
    if len(pdf_files) > 10:
        confirm = input(f"\nAre you sure you want to upload {len(pdf_files)} files? [y/N] ").lower()
        if confirm != 'y':
            print("Upload cancelled")
            return False
    
    success_count = 0
    failed_files = []
    
    for full_path, rel_path in pdf_files:
        print(f"\nUploading {rel_path}...")
        
        if upload_pdf(full_path):
            success_count += 1
        else:
            failed_files.append(rel_path)
            
    print(f"\nUpload Summary:")
    print(f"Successfully uploaded: {success_count}/{len(pdf_files)} files")
    
    if failed_files:
        print("\nFailed uploads:")
        for failed_file in failed_files:
            print(f"- {failed_file}")
    
    return success_count == len(pdf_files)

def main():
    parser = argparse.ArgumentParser(
        description='PDF Processing API Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Configure API key:
    python snh_bridge_util.py configure --api-key YOUR_API_KEY

  Upload a PDF:
    python snh_bridge_util.py upload path/to/your/document.pdf

  Upload all PDFs in a directory:
    python snh_bridge_util.py batch path/to/pdf/directory

  Search documents:
    python snh_bridge_util.py query "your search query here"
""")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', required=True, help='Commands')
    
    # Configure command
    config_parser = subparsers.add_parser('configure', help='Configure API settings')
    config_parser.add_argument('--api-key', required=True, help='API key for authentication')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a PDF file')
    upload_parser.add_argument('file', help='Path to PDF file')
    
    # Batch upload command
    batch_parser = subparsers.add_parser('batch', help='Upload all PDFs in a directory')
    batch_parser.add_argument('directory', help='Directory containing PDF files')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Search through documents')
    query_parser.add_argument('text', help='Search query text')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'configure':
            setup_api_key(args.api_key)
        elif args.command == 'upload':
            if not os.path.exists(args.file):
                print(f"Error: File not found: {args.file}")
                sys.exit(1)
            upload_pdf(args.file)
        elif args.command == 'batch':
            if not os.path.exists(args.directory):
                print(f"Error: Directory not found: {args.directory}")
                sys.exit(1)
            batch_upload(args.directory)
        elif args.command == 'query':
            query_documents(args.text)
        else:
            parser.print_help()
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
