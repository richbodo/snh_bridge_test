# SNH Bridge Test Utility

This repository contains a test utility for the [DataBridge API SNH](https://github.com/richbodo/databridge_api_snh) project. The main script, `snh_bridge_util.py`, provides a command-line interface for testing and interacting with the API.

## Features

- Upload single PDF files
- Batch upload PDFs from directories (including subdirectories)
- Query processed documents
- Secure API key management using Bearer token authentication
- Detailed progress and error reporting

## Installation

1. Clone this repository:
```bash
git clone https://github.com/richbodo/snh_bridge_test.git
cd snh_bridge_test
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
source init.sh

# To deactivate when done
source uninit.sh
```

3. Configure your API key:
```bash
# Option 1: Set environment variable
export SNH_BRIDGE_API_KEY='your_api_key'

# Option 2: Use the configure command
python snh_bridge_util.py configure --api-key your_api_key
```

## Usage

### Upload a Single PDF
```bash
python snh_bridge_util.py upload path/to/your/document.pdf
```

### Batch Upload PDFs
```bash
python snh_bridge_util.py batch path/to/directory
```
This will recursively search the directory and its subdirectories for PDF files.

### Query Documents
```bash
python snh_bridge_util.py query "your search query here"
```

## API Key Management

The utility uses Bearer token authentication for all API requests. Your API key is automatically included in the Authorization header of each request. You can provide your API key in one of these ways:

1. Environment variable: `SNH_BRIDGE_API_KEY`
2. Configuration file: `~/.snh_bridge/config.ini`
3. Command-line configuration

The configuration file is created with restricted permissions (600) to ensure security.

### Authentication Details

All requests to the API include the API key in the Authorization header using the Bearer scheme:
```
Authorization: Bearer your_api_key
```

## Error Handling

The utility provides detailed error messages and debugging information for:
- File access issues
- API communication problems
- Server-side processing errors
- Memory limitations

## Contributing

Please feel free to submit issues and pull requests.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Richard Bodo (richbodo@gmail.com) 