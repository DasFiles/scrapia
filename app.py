from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

def replace_relative_paths_with_base_domain(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')

    links = []
    images = []
    articles = []

    for tag in soup.find_all(['a', 'img', 'p']):
        if tag.name == 'a':
            if 'href' in tag.attrs:
                href = tag['href']
                if href.startswith('/'):
                    # Replace relative path with the base domain
                    tag['href'] = urljoin(base_url, href)
                elif href.startswith('#'):
                    tag['href'] = urljoin(base_url, href)
            links.append({
                'text': tag.get_text(strip=True),
                'href': tag.get('href', '')
            })

        elif tag.name == 'img':
            images.append({
                'alt': tag.get('alt', ''),
                'src': urljoin(base_url, tag.get('src', ''))
            })

        elif tag.name == 'p':
            # Extract text content of the paragraph along with links and references
            paragraph_html = ''
            for element in tag.contents:
                if element.name == 'a':
                    # Extract link or reference associated with text as HTML
                    if 'href' in element.attrs:
                        href = element['href']
                        if href.startswith('/'):
                            # Replace relative path with the base domain
                            element['href'] = urljoin(base_url, href)
                        elif href.startswith('#'):
                            element['href'] = urljoin(base_url, href)
                            
                    link_html = f' <a href="{element.get("href", "")}" target="_blank">{element.get_text(strip=True)}</a>'
                    paragraph_html += link_html

                elif element.name == 'sup':
                    paragraph_html += f' <sup>{element.get_text(strip=True)}</sup>'
                    
                elif isinstance(element, str):
                    # Handle string elements (text content)
                    paragraph_html += f' {element}'
                else:
                    paragraph_html += f"{element}"

            # Append paragraph details to the articles list
            articles.append(paragraph_html.strip())

    # Find all attributes (href, src) containing relative paths
    for tag in soup.find_all(['a', 'link', 'script', 'img', 'iframe']):
        for attribute in ['href', 'src']:
            if attribute in tag.attrs:
                url = tag[attribute]
                if url.startswith('/'):
                    # Replace relative path with the base domain
                    tag[attribute] = urljoin(base_url, url)
                    
                elif url.startswith('#'):
                    tag[attribute] = urljoin(base_url, url)

                # Handle errors for iframes and images
                if tag.name in ['iframe', 'img']:
                    tag[attribute] = handle_loading_errors(tag[attribute])

    return links, images, articles


def handle_loading_errors(url):
    # Add error handling logic here if needed
    # For example, you can replace invalid URLs or hide elements
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return 'about:blank'  # Replace with a default URL or 'about:blank'
    except requests.exceptions.RequestException:
        return 'about:blank'

    return url

@app.route('/')
def index():
    # Get the file URL from the query parameter
    file_url = request.args.get('_url', '')

    if not file_url:
         response = render_template('index.html')
         return response

    # Make an HTTP request to get the content of the file
    response = requests.get(file_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the content using BeautifulSoup or any other appropriate method
        base_url = response.url  # Use the URL after following redirects
        file_content = response.content.decode('utf-8')

        # Replace relative paths with the base domain and categorize elements
        links, images, articles = replace_relative_paths_with_base_domain(file_content, base_url)

        # Pass the content to the template
        response = render_template('c.html', links=links, images=images, articles=articles, file_url=file_url)
        return response
    else:
        error_message = f"Failed to fetch the file. Status code: {response.status_code}"
        return render_template('error.html', error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
