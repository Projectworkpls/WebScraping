RERA Odisha Project Scraper
A Python web scraper that extracts project information from the RERA Odisha website using Selenium and Microsoft Edge WebDriver.

Overview
This scraper automatically extracts the first 6 projects from the RERA Odisha project list and retrieves detailed information including RERA registration numbers, project names, promoter details, addresses, and GST numbers.

Features
✅ Extracts data from the first 6 projects under "Projects Registered"

✅ Handles dynamic content loading with JavaScript

✅ Supports both corporate promoters and individual proprietors

✅ Robust error handling and recovery mechanisms

✅ Saves data to both console output and text file

✅ Uses Microsoft Edge WebDriver for better compatibility

Data Fields Extracted
For each project, the scraper extracts:

RERA Registration No - The official RERA registration number

Project Name - Name of the real estate project

Promoter Name - Company name or individual proprietor name

Promoter Address - Registered office address or permanent address

GST No - GST registration number of the promoter

Important Note
Some projects (like Project 3 in our sample) have individual proprietors instead of companies. In such cases:

The promoter name is listed under "Proprietory Name" instead of "Company Name"

The address is listed under "Permanent Address" instead of "Registered Office Address"

For the sake of simplicity, we treat both corporate promoters and individual proprietors under the same "Promoter Name" field in our output.

Prerequisites
Python 3.7 or higher

Microsoft Edge browser installed

Internet connection
