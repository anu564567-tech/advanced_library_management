/**
 * Chart.js Integration
 * Real-time dashboard statistics visualization
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardCharts();
});

function initializeDashboardCharts() {
    // Fetch dashboard statistics with cache-busting
    const timestamp = new Date().getTime();
    fetch(`/api/dashboard-stats?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            console.log('Dashboard data:', data); // Debug log
            renderCategoryChart(data.categories);
            renderMonthlyChart(data.monthly);
        })
        .catch(error => console.error('Error fetching dashboard stats:', error));
}

function renderCategoryChart(categoriesData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    const labels = Object.keys(categoriesData);
    const data = Object.values(categoriesData);
    
    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(240, 147, 251, 0.8)',
        'rgba(79, 172, 254, 0.8)',
        'rgba(250, 112, 154, 0.8)',
        'rgba(168, 237, 234, 0.8)',
        'rgba(255, 154, 86, 0.8)',
        'rgba(204, 102, 255, 0.8)',
        'rgba(255, 159, 102, 0.8)'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        padding: 20,
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 13,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        family: "'Poppins', sans-serif",
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        family: "'Poppins', sans-serif",
                        size: 13
                    },
                    borderColor: 'rgba(102, 126, 234, 0.5)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ' Books: ' + context.parsed;
                        }
                    }
                }
            }
        }
    });
}

function renderMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthlyChart');
    if (!ctx) return;
    
    console.log('Monthly data received:', monthlyData); // Debug log
    
    // Get current month and create last 6 months
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    
    console.log('Current date:', currentDate, 'Month:', currentMonth, 'Year:', currentYear); // Debug log
    
    // Create labels for last 6 months including current month
    const labels = [];
    const data = [];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let i = 5; i >= 0; i--) {
        const date = new Date(currentYear, currentMonth - i, 1);
        const monthNum = (date.getMonth() + 1).toString().padStart(2, '0');
        const monthName = months[date.getMonth()];
        
        // Add year if it's not the current year
        let label = monthName;
        if (date.getFullYear() !== currentYear) {
            label += ` ${date.getFullYear()}`;
        }
        
        labels.push(label);
        data.push(monthlyData[monthNum] || 0);
        
        console.log(`Month ${monthNum} (${label}): ${monthlyData[monthNum] || 0}`); // Debug log
    }
    
    console.log('Final labels:', labels);
    console.log('Final data:', data);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Books Issued',
                data: data,
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                pointBorderColor: 'rgba(255, 255, 255, 0.8)',
                pointBorderWidth: 2,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        padding: 20,
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 13,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        family: "'Poppins', sans-serif",
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        family: "'Poppins', sans-serif",
                        size: 13
                    },
                    borderColor: 'rgba(102, 126, 234, 0.5)',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)',
                        font: {
                            family: "'Poppins', sans-serif"
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)',
                        font: {
                            family: "'Poppins', sans-serif"
                        }
                    }
                }
            }
        }
    });
}
