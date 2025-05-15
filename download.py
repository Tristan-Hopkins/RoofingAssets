import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

def scrape_stormfighter_flex_colors():
    # Set up the Selenium webdriver (you'll need to have chromedriver installed)
    driver = webdriver.Chrome()
    
    # Navigate to the main StormFighter FLEX page
    driver.get("https://www.tamko.com/flex")
    time.sleep(3)  # Let the page load fully
    
    # Find all slider cards containing color samples
    color_slides = driver.find_elements(By.CSS_SELECTOR, ".slider.stormfighter-slider-container .slider-card")
    
    color_data = []
    
    # First, collect all links
    color_links = []
    for slide in color_slides:
        link = slide.find_element(By.TAG_NAME, "a").get_attribute("href")
        color_name = slide.find_element(By.CSS_SELECTOR, ".color-label").text
        color_links.append((link, color_name))
    
    # Now navigate to each page and collect the images
    for link, color_name in color_links:
        print(f"Processing {color_name}...")
        driver.get(link)
        time.sleep(3)  # Give page time to load
        
        try:
            # Get the hero house image
            house_image_element = driver.find_element(By.CSS_SELECTOR, ".section---house-photo")
            house_image_url = house_image_element.value_of_css_property('background-image')
            house_image_url = house_image_url.replace('url("', '').replace('")', '')
            
            # Get the shingle swatch image
            swatch_element = driver.find_element(By.CSS_SELECTOR, ".styleboard-image")
            swatch_image_url = swatch_element.get_attribute("src")
            
            # Get the angled swatch image if available
            try:
                angled_swatch_element = driver.find_element(By.CSS_SELECTOR, ".section---angled-swatch")
                angled_swatch_url = angled_swatch_element.value_of_css_property('background-image')
                angled_swatch_url = angled_swatch_url.replace('url("', '').replace('")', '')
            except:
                angled_swatch_url = None
            
            # Get the color description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, ".shingle-colors---copy")
                description = description_element.text
            except:
                description = ""
            
            color_data.append({
                "color_name": color_name,
                "description": description,
                "house_image_url": house_image_url,
                "swatch_image_url": swatch_image_url,
                "angled_swatch_url": angled_swatch_url
            })
            
            # Optional: Download the images
            download_directory = "tamko_images"
            os.makedirs(download_directory, exist_ok=True)
            
            if house_image_url:
                download_image(house_image_url, os.path.join(download_directory, f"{color_name.replace(' ', '_')}_house.jpg"))
            
            if swatch_image_url:
                download_image(swatch_image_url, os.path.join(download_directory, f"{color_name.replace(' ', '_')}_swatch.jpg"))
            
            if angled_swatch_url:
                download_image(angled_swatch_url, os.path.join(download_directory, f"{color_name.replace(' ', '_')}_angled.jpg"))
                
        except Exception as e:
            print(f"Error processing {color_name}: {e}")
    
    driver.quit()
    return color_data

def download_image(url, filepath):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded {filepath}")
        else:
            print(f"Failed to download {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    color_data = scrape_stormfighter_flex_colors()
    
    # Print summary of collected data
    print("\nCollected Data Summary:")
    for color in color_data:
        print(f"- {color['color_name']}")
        print(f"  Description: {color['description'][:60]}..." if len(color['description']) > 60 else f"  Description: {color['description']}")
        print(f"  Images: House ({bool(color['house_image_url'])}), Swatch ({bool(color['swatch_image_url'])}), Angled ({bool(color['angled_swatch_url'])})")
        print()
