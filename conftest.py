
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright

@pytest.fixture(scope="function")
def browser_context_args():
    return {"ignore_https_errors": True}

@pytest.fixture(scope="function")
def browser(playwright_instance, browser_context_args):
    browser = playwright_instance.chromium.launch(headless=False)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def context(browser, browser_context_args) -> BrowserContext:
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    return page
