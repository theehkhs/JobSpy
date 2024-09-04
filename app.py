from flask import Flask, jsonify, request
import sys
import os
import json
from flask_cors import CORS

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
    print("HELL")
    # Get parameters from the request
    site_name = request.args.getlist('site_name') or ["indeed"]
    search_term = request.args.get('search_term') or "software engineer"
    location = request.args.get('location') or "Dallas, TX"
    results_wanted = int(request.args.get('results_wanted', 3))
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

    # Filter the job dictionaries to include only the specified fields
    filtered_jobs = [
        {
            "company": job.get("company"),
            "description": job.get("description"),
            "is_remote": job.get("is_remote"),
            "job_url": job.get("job_url"),
            "max_amount": job.get("max_amount"),
            "location": job.get("location")
        }
        for job in jobs_dict_list
    ]

    # Return the filtered jobs list as a JSON response
    return jsonify(filtered_jobs)


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
