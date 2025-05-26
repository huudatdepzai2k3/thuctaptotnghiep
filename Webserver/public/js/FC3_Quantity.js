google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawAllCharts);

function drawAllCharts() {
  drawPieChart();
  drawColumnChart();
  drawHistoryChart();
}

function drawPieChart() {
  var data = google.visualization.arrayToDataTable([
    ['Tình trạng', 'Số lượng'],
    ['Thành công', 65151],
    ['Thất bại', 90]
  ]);

  var options = {
    title: 'Biểu đồ tỷ lệ chia chọn hệ thống',
    pieHole: 0.4,
    colors: ['#00b050', '#ff0000']
  };

  var chart = new google.visualization.PieChart(document.getElementById('piechart'));
  chart.draw(data, options);
}

function drawColumnChart() {
  var data = google.visualization.arrayToDataTable([
    ['Thời gian', 'Đầu cấp 1', 'Đầu cấp 2'],
    ['0:00-2:59', 0, 0],
    ['3:00-5:59', 800, 1600],
    ['6:00-8:59', 0, 0],
    ['9:00-11:59', 500, 1200],
    ['12:00-14:59', 100, 200]
  ]);

  var options = {
    title: 'Biểu đồ sản lượng đầu cấp theo giờ',
    hAxis: {title: 'Thời gian'},
    vAxis: {title: 'Sản lượng'},
    colors: ['#1f77b4', '#ffbf00'],
    isStacked: true
  };

  var chart = new google.visualization.ColumnChart(document.getElementById('columnchart'));
  chart.draw(data, options);
}

function drawHistoryChart() {
  var data = google.visualization.arrayToDataTable([
    ['Tháng', 'Phân loại OK', 'Phân loại NG', 'Hiệu suất'],
    ['11-2020', 50000, 1000, 95],
    ['12-2020', 60000, 2000, 92],
    ['01-2021', 200000, 1000, 98],
    ['02-2021', 100000, 3000, 90],
    ['03-2021', 20000, 2000, 85]
  ]);

  var options = {
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

  var chart = new google.visualization.ComboChart(document.getElementById('historychart'));
  chart.draw(data, options);
}
