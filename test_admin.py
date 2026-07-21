import app
from unittest.mock import MagicMock

app.db = MagicMock()
app.db.inquiries.find.return_value.sort.return_value = []
app.db.vendor_inquiries.find.return_value.sort.return_value = []
app.db.admin_profile.find_one.return_value = None
app.db.reviews.find.return_value.sort.return_value = []
app.db.pricing_packages.find.return_value = []
app.db.services.find.return_value = []
app.db.portfolio.find.return_value = []
app.db.our_story.find_one.return_value = None
app.db.site_config.find_one.return_value = None
app.db.invoices.find.return_value.sort.return_value = []
app.db.client_tickets.find.return_value.sort.return_value = []

with app.app.app_context():
    with app.app.test_request_context('/admin/inquiries'):
        res = app.admin_inquiries()
        with open('output.html', 'w') as f:
            f.write(res)
