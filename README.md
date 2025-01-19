# GoMarble-Assignment
Task: Develop an API server capable of extracting reviews information from any given product page (e.g., Shopify, Amazon). The API should dynamically identify CSS elements of reviews and handle pagination to retrieve all reviews.

Steps to be followed:
1. Insert your OpenAI API Key in app.py where "YOUR_OPENAI_API_KEY" is mentioned.
2. Start the server using the command python app.py
3. Enter the command curl "http://localhost:5000/api/reviews?page={PAGE_URL}" where PAGE_URL is the URL of the product review page.
