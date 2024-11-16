def get_organization_reviews(org_id: int = 1124715036):
    organization_url = f"https://yandex.ru/maps/org/yandeks/{org_id}/reviews/"
    logger.info(f'Start {organization_url=}')
    path = os.path.join(os.getcwd(), 'json')
    if not os.path.exists(path):
        os.makedirs(path)
    file_dttm = dt.datetime.now(dt.timezone.utc)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        driver.get(organization_url)
        total_reviews_text = driver.find_element(by=By.XPATH, value='//*[@class="card-section-header__title _wide"]').text
        total_reviews_int = int(re.sub(r'\D', '', total_reviews_text))

        reviews_selenium_elems = set()
        pbar = tqdm(total=min(total_reviews_int, 1000))
        pbar.set_description("Loading first 1000 reviews on the page")
        
        last_update_time = time.time()
        timeout_limit = 30  # Увеличенный таймаут для подгрузки
        
        while len(reviews_selenium_elems) < 1000:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Дайте время для подгрузки новых данных

            current_reviews = driver.find_elements(by=By.XPATH, value='//*[@class="business-review-view__info"]')
            
            for review_elem in list(current_reviews):
                try:
                    if review_elem not in reviews_selenium_elems:
                        WebDriverWait(driver, 2).until(EC.visibility_of(review_elem))
                        driver.execute_script("arguments[0].scrollIntoView(true);", review_elem)
                        reviews_selenium_elems.add(review_elem)
                        last_update_time = time.time()
                except StaleElementReferenceException:
                    logger.warning("Stale element reference encountered. Retrying on next iteration.")
                    continue

            pbar.update(len(reviews_selenium_elems) - pbar.n)
            time.sleep(0.5)

            if time.time() - last_update_time > timeout_limit:
                logger.warning(f"Timeout reached: No new reviews added in the last {timeout_limit} seconds. Saving data.")
                break
        
        pbar.close()
        logger.info(f"FINI
