# B2B Charge Selling System

A robust Django-based B2B charge selling system that enables sellers to manage credits and sell phone charges. Built with Django 4.2.16 and focusing on scalability, reliability, and atomic transactions.

## Features

- **Credit Management**
  - Secure credit increase/decrease operations
  - Atomic transactions to prevent race conditions
  - Credit balance caching for improved performance

- **Charge Sales**
  - Phone number charge sales tracking
  - Prevention of negative credit balances
  - Comprehensive transaction logging

- **System Security**
  - Protection against double-spending
  - Race condition prevention
  - Atomic transactions for data consistency

- **Performance**
  - Optimized database queries
  - Designed for high concurrent loads

## Technical Stack

- Django 4.2.16
- Django REST Framework 3.14.0
- PostgreSQL
- Python 3.8+

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- virtualenv (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yasamin-khodarahmi/charge-selling-system.git
cd charge_selling_system
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configurations
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

# API Endpoints

## Sellers

### List/Create Sellers
- `GET /api/sellers/` - Get a list of all sellers
- `POST /api/sellers/` - Create a new seller

### Seller Details
- `GET /api/sellers/{id}/` - Get seller details
- `PUT /api/sellers/{id}/` - Update seller details
- `DELETE /api/sellers/{id}/` - Delete a seller

### Credit Management
- `POST /api/sellers/{id}/increase_credit/` - Increase seller's credit
  ```json
  {
    "amount": 100.00
  }
  ```
  Response:
  ```json
  {
    "status": "credit increased",
    "new_credit": 500.00
  }
  ```

- `POST /api/sellers/{id}/sell_charge/` - Process a charge sale
  ```json
  {
    "phone_number": "1234567890",
    "amount": 50.00
  }
  ```
  Response:
  ```json
  {
    "status": "charge sold successfully",
    "remaining_credit": 450.00
  }
  ```

- `GET /api/sellers/{id}/get_credit/` - Get seller's current credit balance
  ```json
  {
    "credit": 450.00
  }
  ```

### Transaction History
- `GET /api/sellers/{id}/get_transactions/` - Get seller's credit transactions (last 100)
- `GET /api/sellers/{id}/get_charge_sales/` - Get seller's charge sales (last 100)

## Phone Numbers

### List/Create Phone Numbers
- `GET /api/phone-numbers/` - Get a list of all phone numbers
- `POST /api/phone-numbers/` - Create a new phone number

### Phone Number Details
- `GET /api/phone-numbers/{id}/` - Get phone number details
- `PUT /api/phone-numbers/{id}/` - Update phone number details
- `DELETE /api/phone-numbers/{id}/` - Delete a phone number

## Credit Transactions

### List Credit Transactions
- `GET /api/credit-transactions/` - Get all credit transactions (last 1000)
  - Optional query parameter: `seller_id`
  ```
  /api/credit-transactions/?seller_id=123
  ```

## Charge Transactions

### List Charge Transactions
- `GET /api/charge-transactions/` - Get all charge transactions (last 1000)
  - Optional query parameters:
    - `seller_id`
    - `phone_number`
  ```
  /api/charge-transactions/?seller_id=123&phone_number=1234567890
  ```

## Error Responses

The API returns standard HTTP status codes:

- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid input (e.g., insufficient credit, duplicate transaction)
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
    "error": "Error message description"
}
```

## Testing

Run the test suite:
```bash
python manage.py test
```

The test suite includes:
- Basic functionality tests
- Concurrent operation tests
- System balance verification
- Credit consistency checks

## Project Structure
```
charge_selling_system/
├── charge_selling/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── project/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt
├── README.md
└── manage.py
```

## Configuration

Key configuration options in `.env`:

```ini
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=b2b_charge_selling
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

## Development Guidelines

1. Follow PEP 8 style guide
2. Write tests for new features
3. Use atomic transactions for credit operations
4. Implement proper error handling
5. Cache frequently accessed data

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
