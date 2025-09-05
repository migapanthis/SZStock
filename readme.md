# SZ Servicing Asset Management System

A web-based application for managing solar PV panels, batteries, inverters, and related equipment across multiple locations. Built with Flask and SQLite for easy deployment and collaboration.

![Solar Asset Management](https://img.shields.io/badge/Flask-2.3+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/solar-asset-management.git
   cd solar-asset-management
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser to: http://localhost:5000
   - Login with: **admin** / **admin123**
   - Change the admin password after first login!

## Usage

### Asset Management
- **Add Assets**: Track serial numbers, manufacturers, models, and locations
- **Update Status**: In Service → Returned → Under Repair → Redeployed
- **Search & Filter**: Quickly find specific assets or groups
- **Export Data**: Download Excel reports for external use

### User Management
- **Multi-Company Support**: Separate access for your warehousing partners
- **Role-Based Access**: Admin users can view audit trails
- **Secure Authentication**: Password hashing and session management

### Audit Trail
- Track all changes to assets
- See who made changes and when
- Before/after values for all updates
- Export audit reports

## Configuration

### Database
- Uses SQLite by default (no setup required)
- Database file: `solar_assets.db`
- Automatically created on first run

### Security Settings
- Change `SECRET_KEY` in production deployment
- Default admin credentials should be changed immediately
- Consider HTTPS for production use

## Project Structure

```
solar-asset-management/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── assets.html
│   └── ...
└── solar_assets.db      # SQLite database (created automatically)
```

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
python app.py
```

### Adding New Asset Types
Edit the asset form template and add new options to the asset type dropdown.

### Database Schema
- **Users**: Authentication and role management
- **Assets**: Equipment tracking and metadata
- **AuditLog**: Change history and user actions

## Deployment

### Production Considerations
1. **Change Secret Key**: Use a secure, random secret key
2. **Database**: Consider PostgreSQL for production
3. **Web Server**: Use Gunicorn + Nginx instead of Flask dev server
4. **HTTPS**: Enable SSL/TLS encryption
5. **Backups**: Set up automated database backups

### Quick Heroku Deployment
```bash
# Install Heroku CLI, then:
heroku create your-app-name
git push heroku main
heroku run python app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Requirements

- Flask >= 2.3.0
- Flask-SQLAlchemy >= 3.0.0
- Flask-Login >= 0.6.0
- Werkzeug >= 2.3.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information about your environment

## Roadmap

- [ ] Integration with SolarZero commissioning app
- [ ] Barcode/QR code scanning
- [ ] Advanced reporting and analytics
- [ ] Bulk import functionality
- [ ] Visibility of parts with FSPs
