<?php
$mysqli = new mysqli("localhost", "root", "", "ten_database");
$mysqli->set_charset("utf8");

$data = [['Tháng', 'Phân loại OK', 'Phân loại NG', 'Hiệu suất']];

$result = $mysqli->query("SELECT month, ok, ng, efficiency FROM classification_history");
while ($row = $result->fetch_assoc()) {
  $data[] = [$row['month'], (int)$row['ok'], (int)$row['ng'], (float)$row['efficiency']];
}

echo json_encode($data);
?>
