// Global variables
let processingStartTime;
let currentView = 'none';
let suspectedAddresses = []; // Store suspected addresses for reference

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set up form submission
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', handleFileUpload);
    
    // Set up button click handlers
    document.getElementById('btn-build-btn').addEventListener('click', buildBTN);
    document.getElementById('btn-pattern-matching').addEventListener('click', runPatternMatching);
    document.getElementById('btn-extension-rules').addEventListener('click', runExtensionRules);
    document.getElementById('btn-withdraw-graph').addEventListener('click', showWithdrawGraph);
    document.getElementById('btn-deposit-graph').addEventListener('click', showDepositGraph);
    document.getElementById('btn-propose-vs-extension').addEventListener('click', showProposeVsExtension);
    document.getElementById('btn-pattern-summary').addEventListener('click', showPatternSummary);
    
    // Set up click handler for the suspected address table
    document.getElementById('suspected-table-body').addEventListener('click', handleSuspectedAddressClick);
});

// Handle file upload
function handleFileUpload(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a file to upload', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading indicator
    showLoading('Uploading file...');
    
    // Send file to server
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showAlert('File uploaded successfully', 'success');
            // Enable the build BTN button
            document.getElementById('btn-build-btn').disabled = false;
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error uploading file: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Build BTN network
function buildBTN() {
    showLoading('Building BTN network...');
    processingStartTime = Date.now();
    
    fetch('/build_btn', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            const processingTime = ((Date.now() - processingStartTime) / 1000).toFixed(2);
            document.getElementById('processing-time').textContent = processingTime + 's';
            
            // Update transaction count
            document.getElementById('transactions-count').textContent = data.transactions_count;
            
            // Update address count if available
            if (data.addresses_count) {
                document.getElementById('addresses-count').textContent = data.addresses_count;
            }
            
            // Enable other buttons
            document.getElementById('btn-pattern-matching').disabled = false;
            
            showAlert('BTN network built successfully', 'success');
            
            // Display transaction previews if needed
            console.log('Transactions:', data.transactions);
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error building BTN network: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Run pattern matching algorithm
function runPatternMatching() {
    // Show loading indicator
    showLoading('Running pattern matching algorithm...');
    
    // Record start time
    processingStartTime = new Date();
    
    // Send request to server
    fetch('/run_pattern_matching', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Store suspected addresses
        suspectedAddresses = data.suspected_addresses;
        
        // Display suspected addresses in table
        displaySuspectedAddresses(suspectedAddresses);
        
        // Enable extension rules button
        document.getElementById('btn-extension-rules').disabled = false;
        
        // Enable visualization buttons
        document.getElementById('btn-withdraw-graph').disabled = false;
        document.getElementById('btn-deposit-graph').disabled = false;
        document.getElementById('btn-propose-vs-extension').disabled = false;
        document.getElementById('btn-pattern-summary').disabled = false;
        
        // Show success message
        showAlert(`Pattern matching completed. Found ${data.suspected_count} suspected addresses.`, 'success');
        
        // Fetch transaction details for the table
        fetchTransactionDetails();
    })
    .catch(error => {
        hideLoading();
        showAlert('Error running pattern matching: ' + error, 'danger');
    });
}

// Fetch detailed transaction information
function fetchTransactionDetails() {
    fetch('/transaction_details')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Transaction details:', data.transaction_details);
            // Transaction details are available for further processing if needed
        } else {
            console.error('Error fetching transaction details:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Run extension rules
function runExtensionRules() {
    showLoading('Running extension rules...');
    processingStartTime = Date.now();
    
    fetch('/extension_rules', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            const processingTime = ((Date.now() - processingStartTime) / 1000).toFixed(2);
            document.getElementById('processing-time').textContent = processingTime + 's';
            
            showAlert(`Extension rules applied successfully. Found ${data.results.rules_applied} addresses in ${data.results.suspected_clusters} clusters.`, 'success');
            
            // After extension rules, refresh transaction details
            fetchTransactionDetails();
            
            // Refresh the suspected addresses display
            fetch('/run_pattern_matching', { method: 'POST' })
            .then(response => response.json())
            .then(patternData => {
                if (patternData.success) {
                    // Update suspected count
                    document.getElementById('suspected-count').textContent = patternData.suspected_count;
                    
                    // Store and display updated suspected addresses
                    suspectedAddresses = patternData.suspected_addresses;
                    displaySuspectedAddresses(patternData.suspected_addresses);
                }
            });
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error running extension rules: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Show withdraw graph
function showWithdrawGraph() {
    showLoading('Generating withdraw graph...');
    currentView = 'withdraw';
    
    fetch('/withdraw_graph')
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Plot the graph
            const plotData = [{
                x: data.data.x,
                y: data.data.y,
                type: data.data.type || 'bar',
                marker: {
                    color: 'rgba(58, 108, 244, 0.7)'
                }
            }];
            
            const layout = {
                title: data.data.title || 'Withdrawal Transactions',
                xaxis: {
                    title: 'Withdrawal Amount'
                },
                yaxis: {
                    title: 'Number of Transactions'
                },
                margin: {
                    l: 50,
                    r: 50,
                    b: 50,
                    t: 80,
                    pad: 4
                }
            };
            
            Plotly.newPlot('chart-container', plotData, layout);
            document.getElementById('chart-title').textContent = data.data.title || 'Withdrawal Transactions';
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error generating withdraw graph: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Show deposit graph
function showDepositGraph() {
    showLoading('Generating deposit graph...');
    currentView = 'deposit';
    
    fetch('/deposit_graph')
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Plot the graph
            const plotData = [{
                x: data.data.x,
                y: data.data.y,
                type: data.data.type || 'bar',
                marker: {
                    color: 'rgba(75, 192, 192, 0.7)'
                }
            }];
            
            const layout = {
                title: data.data.title || 'Deposit Transactions',
                xaxis: {
                    title: 'Address'
                },
                yaxis: {
                    title: 'Deposit Amount'
                },
                margin: {
                    l: 50,
                    r: 50,
                    b: 120,
                    t: 80,
                    pad: 4
                }
            };
            
            Plotly.newPlot('chart-container', plotData, layout);
            document.getElementById('chart-title').textContent = data.data.title || 'Deposit Transactions';
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error generating deposit graph: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Show propose vs extension graph
function showProposeVsExtension() {
    if (currentView === 'propose-vs-extension') {
        return;
    }
    
    currentView = 'propose-vs-extension';
    
    // Show loading indicator
    showLoading('Generating comparison data...');
    
    // Fetch data from server
    fetch('/propose_vs_extension')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showAlert(data.error, 'danger');
                return;
            }
            
            // Create the chart
            const chartData = [{
                x: data.data.x,
                y: data.data.y,
                type: 'bar',
                marker: {
                    color: 'rgba(55, 128, 191, 0.7)'
                }
            }];
            
            const layout = {
                title: data.data.title,
                xaxis: {
                    title: 'Processing Step'
                },
                yaxis: {
                    title: 'Percentage (%)'
                },
                margin: {
                    l: 50,
                    r: 50,
                    t: 50,
                    b: 50
                }
            };
            
            Plotly.newPlot('chart-container', chartData, layout);
            
            // Update chart container title
            document.getElementById('chart-title').textContent = 'Processing Time Distribution';
        })
        .catch(error => {
            hideLoading();
            showAlert('Error fetching data: ' + error, 'danger');
        });
}

function showPatternSummary() {
    if (currentView === 'pattern-summary') {
        return;
    }
    
    currentView = 'pattern-summary';
    
    // Show loading indicator
    showLoading('Generating pattern summary report...');
    
    // Fetch data from server
    fetch('/pattern_summary')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showAlert(data.error, 'danger');
                return;
            }
            
            // Create the pattern summary table
            const patternReport = data.pattern_report;
            const patternTypes = patternReport.pattern_types;
            
            // Create table HTML
            let tableHTML = `
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Pattern Type</th>
                                <th>Count</th>
                                <th>Avg Risk Score</th>
                                <th>Max Risk Score</th>
                                <th>Addresses</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Add rows for each pattern type
            for (const [patternType, stats] of Object.entries(patternTypes)) {
                tableHTML += `
                    <tr>
                        <td>${patternType}</td>
                        <td>${stats.count}</td>
                        <td>${stats.avg_risk_score.toFixed(2)}</td>
                        <td>${stats.max_risk_score.toFixed(2)}</td>
                        <td>${stats.addresses.length}</td>
                    </tr>
                `;
            }
            
            tableHTML += `
                        </tbody>
                    </table>
                </div>
            `;
            
            // Create detailed patterns table
            let detailedTableHTML = `
                <div class="table-responsive mt-4">
                    <h4>Detailed Pattern Information</h4>
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Pattern Type</th>
                                <th>Address</th>
                                <th>Risk Score</th>
                                <th>Details</th>
                                <th>Transaction ID</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Add rows for each pattern
            for (const pattern of patternReport.patterns) {
                detailedTableHTML += `
                    <tr>
                        <td>${pattern.pattern}</td>
                        <td>${pattern.address}</td>
                        <td>${pattern.risk_score.toFixed(2)}</td>
                        <td>${pattern.details}</td>
                        <td>${pattern.transaction_id || 'N/A'}</td>
                    </tr>
                `;
            }
            
            detailedTableHTML += `
                        </tbody>
                    </table>
                </div>
            `;
            
            // Update chart container with tables
            document.getElementById('chart-container').innerHTML = `
                <h3 class="mb-4">Pattern Summary Report</h3>
                <p>Total Patterns Detected: ${patternReport.total_patterns}</p>
                ${tableHTML}
                ${detailedTableHTML}
            `;
            
            // Update chart container title
            document.getElementById('chart-title').textContent = 'Pattern Summary Report';
        })
        .catch(error => {
            hideLoading();
            showAlert('Error fetching data: ' + error, 'danger');
        });
}

// Handle click on suspected address row to show details
function handleSuspectedAddressClick(event) {
    // Find the closest table row
    const row = event.target.closest('tr');
    if (!row) return;
    
    // Get address from the first cell
    const address = row.cells[0].textContent;
    if (!address) return;
    
    // Fetch and display details for this address
    showAddressDetails(address);
}

// Show detailed information for a specific address
function showAddressDetails(address) {
    showLoading(`Loading details for address ${address}...`);
    
    fetch(`/suspected_address_detail/${address}`)
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            displayAddressDetailsModal(data.address_details);
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Error fetching address details: ' + error, 'danger');
        console.error('Error:', error);
    });
}

// Display detailed address information in a modal
function displayAddressDetailsModal(details) {
    // Create modal if it doesn't exist
    let modalElement = document.getElementById('address-detail-modal');
    
    if (!modalElement) {
        const modalHTML = `
            <div class="modal fade" id="address-detail-modal" tabindex="-1" aria-labelledby="modalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalLabel">Address Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="address-detail-content"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modalElement = document.getElementById('address-detail-modal');
    }
    
    // Update modal content
    const contentElement = document.getElementById('address-detail-content');
    
    // Format transaction table
    let transactionsHTML = '';
    if (details.transactions && details.transactions.length > 0) {
        transactionsHTML = `
            <h6 class="mt-4">Transactions</h6>
            <div class="table-responsive">
                <table class="table table-sm table-striped">
                    <thead>
                        <tr>
                            <th>Transaction ID</th>
                            <th>Time</th>
                            <th>Direction</th>
                            <th>Amount</th>
                            <th>Total In/Out</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        details.transactions.forEach(tx => {
            const date = new Date(tx.timestamp * 1000).toLocaleString();
            const direction = tx.is_input ? 'Out' : (tx.is_output ? 'In' : 'Unknown');
            const total = tx.is_input ? tx.total_input : tx.total_output;
            
            transactionsHTML += `
                <tr>
                    <td title="${tx.transaction_id}">${tx.transaction_id.substring(0, 8)}...</td>
                    <td>${date}</td>
                    <td>${direction}</td>
                    <td>${tx.amount.toFixed(8)}</td>
                    <td>${total.toFixed(8)}</td>
                </tr>
            `;
        });
        
        transactionsHTML += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        transactionsHTML = '<p>No transaction details available</p>';
    }
    
    // Format related addresses
    let relatedAddressesHTML = '';
    if (details.related_addresses && details.related_addresses.length > 0) {
        relatedAddressesHTML = `
            <h6 class="mt-4">Related Addresses (Same Cluster)</h6>
            <div class="row">
        `;
        
        details.related_addresses.forEach(addr => {
            relatedAddressesHTML += `
                <div class="col-md-6">
                    <div class="border rounded p-2 mb-2 text-truncate" title="${addr}">
                        ${addr}
                    </div>
                </div>
            `;
        });
        
        relatedAddressesHTML += `
            </div>
            <p class="text-muted small">Showing ${details.related_addresses.length} of ${details.cluster_size} addresses in this cluster</p>
        `;
    }
    
    // Create feature list
    let featureHTML = '';
    if (details.features) {
        featureHTML = `
            <h6 class="mt-4">Address Features</h6>
            <div class="row">
                <div class="col-md-4">
                    <p><strong>Received:</strong> ${details.features.received?.toFixed(8) || 'N/A'}</p>
                    <p><strong>Balance:</strong> ${details.features.balance?.toFixed(8) || 'N/A'}</p>
                </div>
                <div class="col-md-4">
                    <p><strong>In Degree:</strong> ${details.features.in_degree || 'N/A'}</p>
                    <p><strong>Out Degree:</strong> ${details.features.out_degree || 'N/A'}</p>
                </div>
                <div class="col-md-4">
                    <p><strong>Transaction Count:</strong> ${details.features.tx_count || 'N/A'}</p>
                    <p><strong>Centrality:</strong> ${details.features.betweenness_centrality?.toFixed(4) || 'N/A'}</p>
                </div>
            </div>
        `;
    }
    
    // Format reasons for suspicion
    let reasonsHTML = '';
    if (details.reasons && details.reasons.length > 0) {
        reasonsHTML = `
            <h6 class="mt-4">Suspicion Reasons</h6>
            <ul class="list-group mb-3">
        `;
        
        details.reasons.forEach(reason => {
            reasonsHTML += `<li class="list-group-item">${reason}</li>`;
        });
        
        reasonsHTML += '</ul>';
    }
    
    // Assemble all content
    contentElement.innerHTML = `
        <div class="alert alert-danger">
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Suspicious Address</h5>
                <span class="badge bg-danger">Risk Score: ${details.risk_score}/100</span>
            </div>
        </div>
        
        <div class="border rounded p-3 mb-3 text-break">
            <strong>Address:</strong> ${details.address}
        </div>
        
        ${reasonsHTML}
        ${featureHTML}
        ${relatedAddressesHTML}
        ${transactionsHTML}
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Display suspected addresses in the table
function displaySuspectedAddresses(suspectedAddresses) {
    const tableBody = document.getElementById('suspected-table-body');
    tableBody.innerHTML = '';
    
    if (!suspectedAddresses || suspectedAddresses.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" class="text-center">No suspected addresses found</td>';
        tableBody.appendChild(row);
        return;
    }
    
    suspectedAddresses.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'address-row';
        row.style.cursor = 'pointer';
        
        // Format risk badge color based on score
        let badgeClass = 'bg-warning';
        if (item.risk_score >= 70) {
            badgeClass = 'bg-danger';
        } else if (item.risk_score <= 30) {
            badgeClass = 'bg-info';
        }
        
        const reasons = Array.isArray(item.reasons) ? item.reasons.join(', ') : item.reason || '';
        
        row.innerHTML = `
            <td>${item.address}</td>
            <td>${reasons}</td>
            <td>${item.features.received.toFixed(4)}</td>
            <td>${item.features.balance.toFixed(4)}</td>
            <td>${item.features.in_degree}</td>
            <td>${item.features.out_degree}</td>
            <td><span class="badge ${badgeClass}">${item.risk_score || 'N/A'}</span></td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Show alert message
function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.className = `alert alert-${type}`;
    alertContainer.textContent = message;
    alertContainer.classList.remove('d-none');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alertContainer.classList.add('d-none');
    }, 5000);
}

// Show loading indicator
function showLoading(message) {
    const loadingContainer = document.getElementById('loading-container');
    const loadingText = document.getElementById('loading-text');
    
    loadingText.textContent = message || 'Processing...';
    loadingContainer.classList.remove('d-none');
}

// Hide loading indicator
function hideLoading() {
    const loadingContainer = document.getElementById('loading-container');
    loadingContainer.classList.add('d-none');
} 