<?php
$mysqli = new mysqli("localhost", "root", "", "ten_database");
$mysqli->set_charset("utf8");

$data = [['Tình trạng', 'Số lượng']];

$result = $mysqli->query("SELECT status, count FROM status_counts");
while ($row = $result->fetch_assoc()) {
  $data[] = [$row['status'], (int)$row['count']];
}

echo json_encode($data);
?>
