<?php
$mysqli = new mysqli("localhost", "root", "", "ten_database");
$mysqli->set_charset("utf8");

$data = [['Thời gian', 'Đầu cấp 1', 'Đầu cấp 2']];

$result = $mysqli->query("SELECT time_range, cap1, cap2 FROM hourly_output");
while ($row = $result->fetch_assoc()) {
  $data[] = [$row['time_range'], (int)$row['cap1'], (int)$row['cap2']];
}

echo json_encode($data);
?>
