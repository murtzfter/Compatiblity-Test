"


PART 1


"


import csv
import requests
import asyncio
from aiohttp import web
from playwright.sync_api import sync_playwright


async def handle_csv(request):
    try:
        if "file" not in request.post():
            return web.Response(status=400, text="No file provided")

        reader = csv.DictReader(await request.post("file"))
        if "Company Name" not in reader.fieldnames:
            return web.Response(status=400, text="Invalid CSV format. Missing 'Company Name' column.")

        companies = [row["Company Name"] for row in reader]
        companies_with_employee_counts = await get_employee_counts(companies)

        output_file = "company_employees.csv"
        with open(output_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Company Name", "Employee Count"])
            writer.writerows(companies_with_employee_counts)

        return web.FileResponse(output_file)
    except Exception as e:
        return web.Response(status=500, text=str(e))


async def get_employee_counts(companies):
    companies_with_employee_counts = []
    async with sync_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        for company in companies:
            try:
                linkedin_url = await get_linkedin_url(page, company)
                employee_count = await get_employee_count(page, linkedin_url)
                companies_with_employee_counts.append((company, employee_count))
            except Exception as e:
                print(f"Error processing {company}: {str(e)}")
        await browser.close()
    return companies_with_employee_counts


async def get_linkedin_url(page, company_name):
    url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    await page.goto(url)
    await page.wait_for_selector(".search-results__list .search-result__info .search-result__result-link")
    linkedin_url = await page.query_selector_eval(".search-results__list .search-result__info .search-result__result-link", "el => el.href")
    return linkedin_url


async def get_employee_count(page, linkedin_url):
    await page.goto(linkedin_url)
    await page.wait_for_selector(".org-top-card-summary__info-item")
    employee_count_element = await page.query_selector(".org-top-card-summary__info-item")
    employee_count = await employee_count_element.inner_text()
    return employee_count


app = web.Application()
app.router.add_post("/process_csv", handle_csv)

web.run_app(app, port=8080)


"PART 2"

