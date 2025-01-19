from bs4 import BeautifulSoup
from openai import OpenAI
import json
import asyncio
from playwright.async_api import async_playwright
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    # Function to save content to an HTML file
    def save_to_html_file(filename, content):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Saved output to {filename}")

    async def extract_and_save_reviews(url):
        async with async_playwright() as playwright:
            # Launch a browser
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to the product page
            await page.goto(url)  # Replace with the actual product page URL

            # Wait for the page to load
            await page.wait_for_load_state('domcontentloaded')

            # Define potential selectors for reviews sections
            possible_review_selectors = [
                'div[data-review]', 
                '[class*=review]', 
                '[id*=review]', 
                'section[aria-label*=Review]',
                'article:has-text("review")'
            ]

            # Collect matching review sections
            review_sections = []
            for selector in possible_review_selectors:
                elements = page.locator(selector)
                count = await elements.count()
                for i in range(count):
                    # Use innerHTML to extract raw HTML
                    review_sections.append(await elements.nth(i).inner_html())

            if review_sections:
                print('Review sections found and extracted.')

                # Save matching sections to an HTML file
                html_content = '\n<hr>\n'.join(f"<div>{text}</div>" for text in review_sections)
                save_to_html_file('extracted_reviews.html', html_content)
            else:
                print('No review sections found on this page.')

            # Close the browser
            await browser.close()

    def clean_html(file_path, output_path):
        # Open and read the HTML file
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove all unwanted tags
        for tag in soup(['style', 'script', 'input', 'iframe', 'noscript', 'img', 'hr', 'video']):
            tag.decompose()  # Removes the tag and its content

        # Remove <div> tags with no inner text
        for div in soup.find_all('div'):
            if not div.get_text(strip=True):  # Check if div has no visible text
                div.decompose()

        # Remove <a> tags with no inner text
        for a in soup.find_all('a'):
            if not a.get_text(strip=True):  # Check if a has no visible text
                a.decompose()
        
        # Retain only 'class' and 'id' attributes for all tags
        for tag in soup.find_all(True):  # Find all tags
            attributes_to_keep = {'class', 'id'}
            # Filter attributes, keeping only 'class' and 'id'
            tag.attrs = {key: value for key, value in tag.attrs.items() if key in attributes_to_keep}

        # Write the cleaned HTML to an output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(str(soup))

        print(f"Cleaned HTML saved to {output_path}")

    def extract_json():
        # Load the HTML content
        with open("output.html", "r", encoding="utf-8") as file:
            html_content = file.read()

        # OpenAI API key
        client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

        # Prompt for OpenAI to extract data
        prompt = f"""
        The following is an HTML file containing reviews for a product. Extract the structured information for each review into the format by carefully analysing class and the external content for a better distinction. The class names might have the following keywords or related words. Make use of that fact. Do not give me any other information:
        - Rating
        - Title
        - Body
        - Reviewer Name

        Here is the HTML content:
        {html_content}

        Please extract the information in a json file.
        """

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that processes HTML and extracts structured data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000  # Adjust based on the size of the HTML
        )

        data = response.choices[0].message.content

        json_data = data.replace('json', '')
        json_data = json_data.replace('```', '')
        json_data = json.loads(json_data)

        res = {}
        res['Review Count'] = len(json_data)
        res['Reviews'] = json_data

        return res
    
    # Get the 'page' query parameter from the URL
    page_url = request.args.get('page', None)
    
    # Simulate fetching reviews (replace this with actual logic, e.g., database call or external API)
    if page_url:
        asyncio.run(extract_and_save_reviews(page_url))
        clean_html('extracted_reviews.html', 'output.html')
        reviews = extract_json()

        return reviews
    else:
        return jsonify({"status": "error", "message": "Missing 'page' query parameter."}), 400

if __name__ == '__main__':
    app.run(debug=True)