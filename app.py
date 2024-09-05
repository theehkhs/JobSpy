from flask import Flask, jsonify, request
import sys
import os
import json
from flask_cors import CORS
# from google.generativeai import GoogleGenerativeAI  # Assuming you have the Gemini API wrapper
from langchain_google_genai import GoogleGenerativeAI


# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Get the absolute path of the src directory
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))

# import csv
# Add src to the system path
if src_path not in sys.path:
    sys.path.append(src_path)

from jobspy import scrape_jobs

@app.route('/Jobs', methods=['GET', 'POST'])
def get_jobs():
    user_interest = request.headers.get('Email')
    print("user_interest", user_interest)

    # Get parameters from the request
    site_name = request.args.getlist('site_name') or ["indeed"]
    search_term = request.args.get('search_term') or f"{user_interest}"
    location = request.args.get('location') or "Dallas, TX"
    results_wanted = int(request.args.get('results_wanted', 5))
    hours_old = int(request.args.get('hours_old', 72))  
    country_indeed = request.args.get('country_indeed') or 'USA'

    # Scrape the job data
    jobs = scrape_jobs(
        site_name=site_name,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed=country_indeed
    )

    # Convert jobs to a list of dictionaries
    jobs_dict_list = jobs.to_dict(orient='records')

    # Function to clean up text fields (removes asterisks and unwanted characters)
    def clean_text(text):
        if text:
            text_final = text.replace('*', '')  # Remove all asterisks
            text_final = text_final.replace('\n', ' ').replace('▒', '').strip()  # Clean up newlines and other symbols
            return text_final
        return ""

    # Function to clean job data fields
    def clean_job_data(job):
        return {
            "company": clean_text(job.get("company")),
            "description": clean_text(job.get("description")),
            "is_remote": job.get("is_remote"),
            "job_url": clean_text(job.get("job_url")),
            "max_amount": clean_text(str(job.get("max_amount"))),  # In case max_amount is numeric
            "location": clean_text(job.get("location"))
        }

    # Clean all job data fields
    cleaned_jobs = [clean_job_data(job) for job in jobs_dict_list]

    print("cleaned_jobs", cleaned_jobs)
    
    # Initialize the Gemini LLM API
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = GoogleGenerativeAI(model="gemini-pro", api_key=api_key)

    # Function to summarize job details using Gemini
    def summarize_job(job):
        prompt = f"""
            Summarize the following job posting with brief details: 
            - Company: {job['company']}
            - Description: {job['description']}
            - Is Remote: {'Yes' if job['is_remote'] else 'No'}
            - Max Salary: {job['max_amount']}
            - Location: {job['location']}
            - Job URL: {job['job_url']}

            Keep the summary concise and professional.
        """
        response = llm.invoke(prompt)
        final_result = clean_text(response)
        print("final_result", final_result)
        return final_result  # Assuming it returns a summarized string

    # Go through cleaned jobs and summarize each job description
    summarized_jobs = [
        {
            "company": job["company"],
            "description": summarize_job(job),
            "is_remote": job["is_remote"],
            "job_url": job["job_url"],
            "max_amount": job["max_amount"],
            "location": job["location"]
        }
        for job in cleaned_jobs
    ]

    print("Summarized Jobs: ", summarized_jobs)

    # Return the summarized jobs list as a JSON response
    return jsonify(summarized_jobs)


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
