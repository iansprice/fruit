from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from models import Fruit  # Import your model
from validation import validate_parameters

app = Flask(__name__, static_folder='frontend/build', static_url_path='')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 7})
Session = sessionmaker(bind=engine)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500


# Serve React App
@app.route('/')
def serve_react_app():
    """
    Serves entry file for our frontend (from frontend/build)
    """
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static_files(path):
    """
    Serves static files (CSS, JS, etc.) for our frontend (relative to frontend/build)
    """
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/harvest-estimate', methods=['POST'])
def get_harvest_estimate():
    """
    Calculates harvest estimates for fruits within specified diameter range

    Request Body:
    {
        "scan_date": "2024-10-01",
        "harvest_date": "2024-10-11",
        "growth_rate": 1000.0,
        "min_diameter": 5.0,
        "max_diameter": 20.0
    }

    Returns:
    {
        "status": "success",
        "data": {
            "fruits": [...],
            "statistics": {...},
            "parameters": {...}
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate parameters
        scan_date, harvest_date, growth_rate, min_diameter, max_diameter = validate_parameters(data)

        # Create database session
        session = Session()

        try:
            # Calculate harvest estimates
            harvest_data = Fruit.calculate_harvest_estimates(
                session, scan_date, harvest_date, growth_rate, min_diameter, max_diameter
            )

            # Get summary statistics
            statistics = Fruit.get_harvest_statistics(
                session, scan_date, harvest_date, growth_rate, min_diameter, max_diameter
            )

            # Add additional calculated fields
            days_delta = (harvest_date - scan_date).days
            statistics['days_between_scan_and_harvest'] = days_delta
            statistics['total_growth_per_fruit'] = days_delta * growth_rate

            response_data = {
                'status': 'success',
                'data': {
                    'fruits': harvest_data,
                    'statistics': statistics,
                    'parameters': {
                        'scan_date': scan_date.isoformat(),
                        'harvest_date': harvest_date.isoformat(),
                        'growth_rate': growth_rate,
                        'min_diameter': min_diameter,
                        'max_diameter': max_diameter,
                        'days_delta': days_delta
                    }
                }
            }

            return jsonify(response_data)

        finally:
            session.close()

    except ValueError as e:
        return jsonify({'error': 'Validation error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.route('/api/harvest-histogram', methods=['POST'])
def get_harvest_histogram():
    """
    Gets histogram data for predicted harvest volumes

    Returns the same data as harvest-estimate but formatted for histogram display
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Get number of bins for histogram (optional parameter)
    num_bins = data.get('num_bins', 20)

    # Validate parameters
    scan_date, harvest_date, growth_rate, min_diameter, max_diameter = validate_parameters(data)

    session = Session()

    try:
        # Get harvest data
        harvest_data = Fruit.calculate_harvest_estimates(
            session, scan_date, harvest_date, growth_rate, min_diameter, max_diameter
        )

        if not harvest_data:
            return jsonify({
                'status': 'success',
                'data': {
                    'histogram': [],
                    'statistics': {
                        'count': 0,
                        'average_predicted_volume': 0,
                        'total_predicted_volume': 0
                    }
                }
            })

        # Extract predicted volumes for histogram
        predicted_volumes = [fruit['predicted_harvest_volume'] for fruit in harvest_data]

        # Create histogram bins
        min_vol = min(predicted_volumes)
        max_vol = max(predicted_volumes)
        bin_width = (max_vol - min_vol) / num_bins if max_vol > min_vol else 1

        histogram = []
        for i in range(num_bins):
            bin_start = min_vol + (i * bin_width)
            bin_end = bin_start + bin_width

            # Count fruits in this bin
            count = sum(1 for vol in predicted_volumes if bin_start <= vol < bin_end)

            # Handle the last bin to include the maximum value
            if i == num_bins - 1:
                count = sum(1 for vol in predicted_volumes if bin_start <= vol <= bin_end)

            histogram.append({
                'bin_start': round(bin_start, 2),
                'bin_end': round(bin_end, 2),
                'bin_center': round(bin_start + bin_width / 2, 2),
                'count': count,
                'percentage': round((count / len(predicted_volumes)) * 100, 2) if predicted_volumes else 0
            })

        # Get statistics
        statistics = Fruit.get_harvest_statistics(
            session, scan_date, harvest_date, growth_rate, min_diameter, max_diameter
        )

        return jsonify({
            'status': 'success',
            'data': {
                'histogram': histogram,
                'statistics': statistics,
                'parameters': {
                    'scan_date': scan_date.isoformat(),
                    'harvest_date': harvest_date.isoformat(),
                    'growth_rate': growth_rate,
                    'min_diameter': min_diameter,
                    'max_diameter': max_diameter,
                    'num_bins': num_bins
                }
            }
        })

    finally:
        session.close()



@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check to check DB connectivity
    """
    try:
        session = Session()
        session.execute(text('SELECT 1'))
        session.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)