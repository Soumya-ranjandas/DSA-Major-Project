# GoParking – Parking Allotment Management System

## Project Overview

GoParking is a parking lot management system developed using Core Java, Data Structures and Algorithms (DSA), and Streamlit. It helps manage vehicle entry, parking slot allocation, vehicle removal, and vehicle searches through a user-friendly web interface.

## Objectives

* Automate parking slot allocation.
* Allocate the nearest available parking slot.
* Track occupied and available parking spaces.
* Search vehicles using registration details and other attributes.
* Demonstrate practical applications of Data Structures and Algorithms.

## Technologies Used

* **Java:** Parking management backend.
* **Python and Streamlit:** Web interface.
* **TreeSet:** Maintain parking slots in sorted order.
* **HashMap:** Support efficient vehicle and slot lookups.
* **ArrayList:** Store and process collections of parking information.
* **SQLite:** Store application records, where configured.

## Main Features

* User authentication and admin access.
* Vehicle parking and removal.
* Automatic parking slot allocation.
* Parking status dashboard.
* Vehicle search functionality.
* Duplicate vehicle registration validation.
* Slot availability tracking.

## Project Structure

* `GoParking/` – Main application source code.
* `docs/` – Project report and documentation.
* `screenshots/` – Application screenshots.
* `PPT.pdf` – Project presentation, if included.

## How to Run

1. Install Java JDK and Python.
2. Install Streamlit using `python -m pip install streamlit`.
3. Open the project folder in Command Prompt.
4. Compile the Java source files using the instructions applicable to the Java backend folder.
5. Start the Java backend using the project's configured startup command.
6. In another Command Prompt window, run `python -m streamlit run app.py` from the folder containing the Streamlit application.

Refer to the source code and project documentation for the exact file locations and configuration.

## Data and Security

This project uses local application storage. Do not commit database files, real user data, passwords, secret keys, or other credentials to a public repository.

## Author

Soumya Ranjan Dash & Tesh Kumar Sahu

## Academic Project

B.Tech Computer Science and Engineering – Minor/Major Project
