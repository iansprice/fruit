import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Calendar, TrendingUp, Sliders, Play, AlertCircle, CheckCircle } from 'lucide-react';

const HarvestEstimationApp = () => {
  const [formData, setFormData] = useState({
    scanDate: '',
    harvestDate: '',
    growthRate: '',
    minDiameter: 20,
    maxDiameter: 120
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(''); // Clear errors when user starts typing
  };

  const validateForm = () => {
    if (!formData.scanDate) return 'Please select a scan date';
    if (!formData.harvestDate) return 'Please select a harvest date';
    if (!formData.growthRate) return 'Please enter a growth rate';

    const scanDate = new Date(formData.scanDate);
    const harvestDate = new Date(formData.harvestDate);

    if (harvestDate <= scanDate) return 'Harvest date must be after scan date';

    const growthRate = parseFloat(formData.growthRate);
    if (isNaN(growthRate) || growthRate < 0) return 'Growth rate must be a positive number';

    if (formData.minDiameter >= formData.maxDiameter) {
      return 'Minimum diameter must be less than maximum diameter';
    }

    return null;
  };

  const handleSubmit = async () => {

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const requestData = {
        scan_date: formData.scanDate,
        harvest_date: formData.harvestDate,
        growth_rate: parseFloat(formData.growthRate),
        min_diameter: formData.minDiameter,
        max_diameter: formData.maxDiameter,
        num_bins: 20
      };

      const response = await fetch('/api/harvest-histogram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to calculate harvest estimate');
      }

      const data = await response.json();
      setResults(data.data);
    } catch (err) {
      setError(`Error: ${err.message}`);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatHistogramData = (histogram) => {
    return histogram.map(bin => ({
      range: `${bin.bin_start?.toFixed(1).toLocaleString('en-US')}-${bin.bin_end?.toFixed(1).toLocaleString('en-US')}`,
      count: bin.count,
      percentage: bin.percentage,
      volume: bin.bin_center
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-8 flex justify-between  gap-3">
            <div class="flex">
                Fruit Harvest Estimation
            </div>
            <img src="logo.png" class="h-8"/>
          </h1>

          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Scan Date */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Calendar className="w-4 h-4" />
                  Scan Date
                </label>
                <input
                  type="date"
                  value={formData.scanDate}
                  onChange={(e) => handleInputChange('scanDate', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Harvest Date */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Calendar className="w-4 h-4" />
                  Harvest Date
                </label>
                <input
                  type="date"
                  value={formData.harvestDate}
                  onChange={(e) => handleInputChange('harvestDate', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>
            </div>

            {/* Growth Rate */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <TrendingUp className="w-4 h-4" />
                Fruit Growth Rate (mm³/day)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.growthRate}
                onChange={(e) => handleInputChange('growthRate', e.target.value)}
                placeholder="e.g., 1000.0"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            {/* Diameter Range Selector */}
            <div className="space-y-4">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Sliders className="w-4 h-4" />
                Fruit Diameter Range (mm)
              </label>

              <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-xs text-gray-600 mb-2 block">Diameter Range</label>

                  <div className="relative pt-1 pb-8">
                    {/* Track */}
                    <div className="relative h-2 bg-gray-200 rounded-lg">
                      {/* Active range highlight */}
                      <div
                        className="absolute h-2 bg-blue-500 rounded-lg"
                        style={{
                          left: `${((formData.minDiameter - 20) / (120 - 20)) * 100}%`,
                          right: `${100 - ((formData.maxDiameter - 20) / (120 - 20)) * 100}%`
                        }}
                      />
                    </div>

                    {/* Min handle */}
                    <input
                      type="range"
                      min="20"
                      max="120"
                      step="1"
                      value={formData.minDiameter}
                      onChange={(e) => {
                        const value = parseInt(e.target.value);
                        if (value <= formData.maxDiameter) {
                          handleInputChange('minDiameter', value);
                        }
                      }}
                      className="absolute w-full h-2 top-1 bg-transparent appearance-none cursor-pointer pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-600 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-md [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-blue-600 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:shadow-md"
                    />

                    {/* Max handle */}
                    <input
                      type="range"
                      min="20"
                      max="120"
                      step="1"
                      value={formData.maxDiameter}
                      onChange={(e) => {
                        const value = parseInt(e.target.value);
                        if (value >= formData.minDiameter) {
                          handleInputChange('maxDiameter', value);
                        }
                      }}
                      className="absolute w-full h-2 top-1 bg-transparent appearance-none cursor-pointer pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-600 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-md [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-blue-600 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:shadow-md"
                    />

                    {/* Value labels */}
                    <div className="flex justify-between mt-2 text-sm font-medium text-gray-700">
                      <span>{formData.minDiameter} mm</span>
                      <span>{formData.maxDiameter} mm</span>
                    </div>
                  </div>

                  <div className="text-sm text-gray-600 text-center">
                    Selected range: {formData.minDiameter}mm - {formData.maxDiameter}mm
                  </div>
                </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Calculate Harvest Estimate
                </>
              )}
            </button>
          </div>

          {/* Results Section */}
          {results && (
            <div className="mt-8 space-y-6">
              <div className="border-t pt-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                  <CheckCircle className="text-green-600" />
                  Harvest Estimation Results
                </h2>

                {/* Statistics Cards */}
                {results.statistics.count > 0 && <div className="grid md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {results.statistics.count.toLocaleString()}
                    </div>
                    <div className="text-sm text-blue-700">Fruits Found</div>
                  </div>

                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {results.statistics.average_predicted_volume.toLocaleString(undefined, {maximumFractionDigits: 0})}
                    </div>
                    <div className="text-sm text-green-700">Avg Volume (mm³)</div>
                  </div>

                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {results.statistics.average_diameter?.toLocaleString('en-US')}
                    </div>
                    <div className="text-sm text-purple-700">Avg Diameter (mm)</div>
                  </div>

                  <div className="bg-orange-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {(results.statistics.total_predicted_volume / 1000000)?.toFixed(1).toLocaleString('en-US')}
                    </div>
                    <div className="text-sm text-orange-700">Total Vol (cm³)</div>
                  </div>
                </div>}

                {/* Histogram */}
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">
                    Predicted Volume Distribution
                  </h3>

                  {results.histogram && results.histogram.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={formatHistogramData(results.histogram)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="range"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          fontSize={12}
                        />
                        <YAxis />
                        <Tooltip
                          formatter={(value, name) => [
                            name === 'count' ? `${value} fruits` : `${value}%`,
                            name === 'count' ? 'Count' : 'Percentage'
                          ]}
                          labelFormatter={(label) => `Volume Range: ${label.toLocaleString('en-US')} mm³`}
                        />
                        <Bar
                          dataKey="count"
                          fill="#16a34a"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      No fruits found within the specified diameter range.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HarvestEstimationApp;