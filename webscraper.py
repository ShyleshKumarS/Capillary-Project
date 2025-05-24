from playwright.sync_api import sync_playwright # type: ignore
import pandas as pd
import time

def scrape_puma(playwright):
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="C:/playwright", 
        channel="chrome",
        headless=False,
        no_viewport=True,
    )

    page = browser.new_page()

    page.goto("https://in.puma.com/in/en/puma-sale-collection?sort=Discount-high-to-low")

 # Home Page Products
    for _ in range(6):  
        page.mouse.wheel(0, 5000)
        time.sleep(2)

    product_links = []
    product_elements = page.locator("a[data-test-id='product-list-item-link']")
    for element in product_elements.element_handles():
        href = element.get_attribute("href")
        if href:
            product_links.append(f"https://in.puma.com{href}")

    print(f"Found {len(product_links)} product links")

    all_products = []

    product_links = product_links[:5]
    print(f"Simplicity: Found {len(product_links)} product links")
# Product Page Details
    for link in product_links:
        try:
            page.goto(link)
            time.sleep(5)

            product = {
                "Product Link": link,
                "Title": "",
                "Promotion": "",
                "Actual Price": "",
                "Discounted Price": "",
                "Category": "",
                "Description": "",
                "Sizes": []
            }

            title = page.locator("h1[data-test-id='pdp-title']")
            if title.count() > 0:
                product["Title"] = title.inner_text()

            promo = page.locator("p[data-test-id='promotion-callout-message']")
            if promo.count() > 0:
                product["Promotion"] = promo.inner_text()

            actual_price = page.locator("span[data-test-id='item-price-pdp']")
            if actual_price.count() > 0:
                product["Actual Price"] = actual_price.inner_text()
                
            discounted_price = page.locator("span[data-test-id='item-sale-price-pdp']")
            if discounted_price.count() > 0:
                product["Discounted Price"] = discounted_price.inner_text()


            category = title.inner_text()
            category = category.split()[-1]
            product["Category"] = category

            try:
                page.wait_for_selector("div[data-test-id='pdp-product-description'] > div", timeout=10000)
                
                read_more = page.locator("button:has-text('Read More')")
                if read_more.count() > 0:
                    read_more.click()
                    time.sleep(5)

                product_story_divs = page.locator("#product-story h3", has_text="Product Story").nth(0).locator("xpath=..").locator("xpath=following-sibling::div[1]")
                if product_story_divs.count() > 0:
                    product["Description"] = product_story_divs.nth(0).inner_text().strip()
                else:
                    product["Description"] = "N/A"
                    
            except Exception as e:
                print(f"Error loading description: {e}")
                

            size_labels = page.locator("div#size-picker label")

            product["Sizes"] = []
            for size_label in size_labels.element_handles():
                try:
                    size_text = size_label.query_selector('[data-content="size-value"]').inner_text()
                    product["Sizes"].append(size_text.strip())
                except:
                    continue
                
            all_products.append(product)

        except Exception as e:
            print(f"Error scraping {link}: {e}")

    browser.close()
    return all_products


def run_scraper():
    with sync_playwright() as playwright:
        products = scrape_puma(playwright)
        df = pd.DataFrame(products)
        df.to_csv("puma_sale_products_refreshed.csv", index=False)
        print("Saved to puma_sale_products.csv")
