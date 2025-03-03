# MedicalAI

MedicalAI is an AI-powered medical analysis tool designed to assist healthcare professionals with data-driven insights. It leverages machine learning and geospatial analysis to provide valuable support in medical decision-making.

## Features
- AI-powered medical data analysis
- Geospatial data processing using `geopy`
- Machine learning capabilities with `scikit-learn`
- Web-based API using `Flask` and `Flask-CORS`
- Data manipulation with `pandas` and `numpy`

## Installation
To install and set up MedicalAI, follow these steps:

### Prerequisites
Ensure you have Python 3.8 or later installed on your system.

### Clone the Repository
```bash
git clone https://github.com/jonathanMusumba/MedicalAI.git
cd MedicalAI
```

### Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage
To start the MedicalAI application, run:
```bash
python app.py
```
The application will be accessible at `http://127.0.0.1:5000/`.

## Dependencies
MedicalAI requires the following Python packages:
```
blinker==1.9.0
click==8.1.8
colorama==0.4.6
Flask==3.1.0
flask-cors==5.0.1
geographiclib==2.0
geopy==2.4.1
itsdangerous==2.2.0
Jinja2==3.1.5
joblib==1.4.2
MarkupSafe==3.0.2
numpy==2.2.3
pandas==2.2.3
python-dateutil==2.9.0.post0
pytz==2025.1
scikit-learn==1.6.1
scipy==1.15.2
six==1.17.0
threadpoolctl==3.5.0
tzdata==2025.1
Werkzeug==3.1.3
```

## Contribution
Contributions are welcome! To contribute:
1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For any questions or inquiries, feel free to open an issue or contact us at `your-email@example.com`.

