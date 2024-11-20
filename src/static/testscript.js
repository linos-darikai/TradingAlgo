document.addEventListener('DOMContentLoaded', function() {
    // Create chart container with fixed dimensions
    const container = document.createElement('div');
    container.className = 'chart-container';
    container.style.width = '1000px';
    container.style.height = '550px';
    container.style.padding = '20px';
    container.style.float = 'left';
    
    const header = document.createElement('div');
    header.innerHTML = `
        <h2>S&P 500 (SPX) Historical Data</h2>
        <p id="lastUpdate">Last updated: Never</p>
    `;
    
    const canvas = document.createElement('canvas');
    canvas.id = 'stockChart';
  

    
    container.appendChild(header);
    container.appendChild(canvas);
    document.body.appendChild(container);

    // Initialize chart
    const ctx = canvas.getContext('2d');
    let stockChart = null;
    let currentData = [];
    let fullData = [];
    let currentIndex = 0;
    
    // Define the window size (number of data points to show at once)
    const WINDOW_SIZE = 50;
    // Update interval in milliseconds (1 minute = 60000 ms)
    const UPDATE_INTERVAL = 2000;

    function transformData(rawData) {
        return Object.entries(rawData).map(([_, dataPoint]) => ({
            // Use the timestamp directly from pandas (index 8)
            timestamp: dataPoint[7],
            open: dataPoint[0],
            high: dataPoint[1],
            low: dataPoint[2],
            close: dataPoint[3],
            volume: dataPoint[4],
            dividends: dataPoint[5],
            splits: dataPoint[6],
            decision: dataPoint[8],
        }));
    }

    function formatDate(timestamp) {
        return new Date(timestamp).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    function initializeChart() {
        if (stockChart) {
            stockChart.destroy();
        }

        stockChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Close',
                        data: [],
                        borderColor: 'rgb(37, 99, 235)',
                        borderWidth: 2,
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'Open',
                        data: [],
                        borderColor: 'rgb(5, 150, 105)',
                        borderWidth: 1,
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'High',
                        data: [],
                        borderColor: 'rgb(220, 38, 38)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'Low',
                        data: [],
                        borderColor: 'rgb(202, 138, 4)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        tension: 0.1,
                        fill: false
                    },
                
                    {
                        label: 'Decision',
                        data: [],
                    }
        

                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 0 
                },
                scales: {
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label === 'Decision') {
                                    return `Decision: ${context.parsed.y}`;
                                }
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                            }
                            
                        }
                    }
                }
            }
        });
    }

    function addDataPoint() {
        if (currentIndex < fullData.length) {
            const point = fullData[currentIndex];
            currentData.push(point);
            
            // To old data points if we exceed the window size
            if (currentData.length > WINDOW_SIZE) {
                currentData.shift();
                stockChart.data.labels.shift();
                stockChart.data.datasets.forEach(dataset => {
                    dataset.data.shift();
                });
            }
            
            stockChart.data.labels.push(formatDate(point.timestamp));
            stockChart.data.datasets[0].data.push(point.close);
            stockChart.data.datasets[1].data.push(point.open);
            stockChart.data.datasets[2].data.push(point.high);
            stockChart.data.datasets[3].data.push(point.low);
            // to add here the same line but for decision
            stockChart.data.datasets[4].data.push(point.decision);
            stockChart.update('none'); 
            
            currentIndex++;

            setTimeout(addDataPoint, UPDATE_INTERVAL);
        } else {
            // All points added, schedule next data fetch
            setTimeout(fetchData, UPDATE_INTERVAL);
        }
    }

    function updateChart(data) {
        fullData = transformData(data);
        currentData = [];
        currentIndex = 0;
        
        initializeChart();
        addDataPoint(); // Start adding points
    }

    async function fetchData() {
        try {
            const response = await fetch('/data');
            const data = await response.json();
            updateChart(data);
            
            document.getElementById('lastUpdate').textContent = 
                'Last updated: ' + new Date().toLocaleString();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    fetchData();
});