google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawAllCharts);

function drawAllCharts() {
  drawPieChart();
  drawColumnChart();
  drawHistoryChart();
}

function drawPieChart() {
  fetch('get_pie_data.php')
    .then(response => response.json())
    .then(dataArray => {
      const data = google.visualization.arrayToDataTable(dataArray);
      const options = {
        title: 'Biểu đồ tỷ lệ chia chọn hệ thống',
        pieHole: 0.4,
        colors: ['#00b050', '#ff0000']
      };
      const chart = new google.visualization.PieChart(document.getElementById('piechart'));
      chart.draw(data, options);
    });
}

function drawColumnChart() {
  fetch('get_column_data.php')
    .then(response => response.json())
    .then(dataArray => {
      const data = google.visualization.arrayToDataTable(dataArray);
      const options = {
        title: 'Biểu đồ sản lượng đầu cấp theo giờ',
        hAxis: {title: 'Thời gian'},
        vAxis: {title: 'Sản lượng'},
        colors: ['#1f77b4', '#ffbf00'],
        isStacked: true
      };
      const chart = new google.visualization.ColumnChart(document.getElementById('columnchart'));
      chart.draw(data, options);
    });
}

function drawHistoryChart() {
  fetch('get_history_data.php')
    .then(response => response.json())
    .then(dataArray => {
      const data = google.visualization.arrayToDataTable(dataArray);
      const options = {
        title: 'Lịch sử phân loại hàng',
        vAxes: {
          0: {title: 'Sản lượng (ngàn đơn)'},
          1: {title: 'Hiệu suất (%)'}
        },
        seriesType: 'bars',
        series: {
          0: {targetAxisIndex: 0, color: '#00b050'},
          1: {targetAxisIndex: 0, color: '#ff0000'},
          2: {type: 'line', targetAxisIndex: 1, color: '#00b0f0'}
        }
      };
      const chart = new google.visualization.ComboChart(document.getElementById('historychart'));
      chart.draw(data, options);
    });
}
