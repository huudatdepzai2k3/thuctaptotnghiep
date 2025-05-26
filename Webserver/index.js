//////////////////////CẤU HÌNH KẾT NỐI KEPWARE////////////////////
const {TagBuilder, IotGateway} = require('kepserverex-js');
const tagBuilder = new TagBuilder({ namespace: 'Channel1.Device1' });
const iotGateway = new IotGateway({
    host: '127.0.0.1',
    port: 5000
});

// Khai báo SQL
var mysql = require('mysql');
var sqlcon = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "123456",
  database: "SQL_PLC",
  dateStrings:true
});

// /////////////////////////THIẾT LẬP KẾT NỐI WEB/////////////////////////
var express = require("express");
var app = express();
app.use(express.static("public"));
app.set("view engine", "ejs");
app.set("views", "./views");
var server = require("http").Server(app);
var io = require("socket.io")(server);
server.listen(3000);
// Home calling
app.get("/", function(req, res){
    res.render("home")
});
//

/////////////HÀM ĐỌC/GHI DỮ LIỆU XUỐNG KEPWARE(PLC)//////////////
//Đọc dữ liệu
var tagArr = [];
function fn_tagRead(){
    iotGateway.read(TagList).then((data)=>{
        var lodash = require('lodash');
        tagArr = lodash.map(data, (item) => item.v);
        console.log(tagArr);
    });
}
// Ghi dữ liệu
function fn_Data_Write(tag,data){
    tagBuilder.clean();
    const set_value = tagBuilder
        .write(tag,data)
        .get();
    iotGateway.write(set_value);
}
///////////////////////////ĐỊNH NGHĨA TAG////////////////////////
// Khai báo tag input
var quantity_adress_1 = "'" + tagArr[1] + "',"
var quantity_adress_2 = "'" + tagArr[2] + "',"
var quantity_adress_3 = "'" + tagArr[3] + "',"
var quantity_adress_4 = "'" + tagArr[4] + "',"
var quantity_adress_5 = "'" + tagArr[5] + "',"
var quantity_adress_6 = "'" + tagArr[6] + "'"

// === Đọc dữ liệu hmi ===
var state_motor = "state_motor";
var state_auto = "state_auto";
var state_cam_bien_1 = "state_cam_bien_1";
var state_cam_bien_2 = "state_cam_bien_2";
var state_cam_bien_3 = "state_cam_bien_3";
var state_cam_bien_4 = "state_cam_bien_4";
var state_cam_bien_5 = "state_cam_bien_5";
var state_cam_bien_6 = "state_cam_bien_6";

var state_xi_lanh_1 = "state_xi_lanh_1";
var state_xi_lanh_2 = "state_xi_lanh_2";
var state_xi_lanh_3 = "state_xi_lanh_3";
var state_xi_lanh_4 = "state_xi_lanh_4";
var state_xi_lanh_5 = "state_xi_lanh_5";

// Đọc dữ liệu
const TagList = tagBuilder
.read(quantity_adress_1)
.read(quantity_adress_2)
.read(quantity_adress_3)
.read(quantity_adress_4)
.read(quantity_adress_5)
.read(quantity_adress_6)
.read(state_cam_bien_1)
.read(state_cam_bien_2)
.read(state_cam_bien_3)
.read(state_cam_bien_4)
.read(state_cam_bien_5)
.read(state_cam_bien_6)
.read(state_xi_lanh_1)
.read(state_xi_lanh_2)
.read(state_xi_lanh_3)
.read(state_xi_lanh_4)
.read(state_xi_lanh_5)
.read(state_motor)
.read(state_auto)
.get();

///////////////////////////QUÉT DỮ LIỆU////////////////////////
// Tạo Timer quét dữ liệu
setInterval(
    () => fn_read_data_scan(),
    1000 //1000ms = 1s
);
// Quét dữ liệu
function fn_read_data_scan(){
    fn_tagRead();   // Đọc giá trị tag
}


// Khai báo tag output
var button_state = "state_button"

// ///////////TRUYỀN NHẬN DỮ LIỆU VỚI TRÌNH DUYỆT WEB///////////////////
io.on("connection", function(socket){
    // Bật tắt đây chuyền
    socket.on("Client-send-cmdM1", function(){
        if (button_state == 0) {
            fn_Data_Write(button_state,1);
        } else {
            fn_Data_Write(button_state,0);
        }
    });
});


// Ghi dữ liệu vào SQL
var sqlins_done = false; // Biến báo đã ghi xong dữ liệu
function fn_sql_insert(){
    var trigger = tagArr[0];  // Trigger đọc về từ PLC
    var sqltable_Name = "plc_data";
    // Lấy thời gian hiện tại
    var tzoffset = (new Date()).getTimezoneOffset() * 60000; //Vùng Việt Nam (GMT7+)
    var temp_datenow = new Date();
 var timeNow = (new Date(temp_datenow - tzoffset)).toISOString().slice(0, -1).replace("T"," ");
    var timeNow_toSQL = "'" + timeNow + "',";

    // Dữ liệu đọc lên từ các tag
    var data_quantity_adress_1 = "'" + tagArr[1] + "',";
    var data_quantity_adress_2 = "'" + tagArr[2] + "',";
    var data_quantity_adress_3 = "'" + tagArr[3] + "',";
    var data_quantity_adress_4 = "'" + tagArr[4] + "',";
    var data_quantity_adress_5 = "'" + tagArr[5] + "',";
    var data_quantity_adress_6 = "'" + tagArr[6] + "'";
    
    // Ghi dữ liệu vào SQL
    if (trigger == true & trigger != sqlins_done)
    {
        var sqlins1 = "INSERT INTO "
                    + sqltable_Name
                    + " (date_time, data_quantity_adress_1, data_quantity_adress_2, data_quantity_adress_3, data_quantity_adress_4, data_quantity_adress_5, data_quantity_adress_6) VALUES (";
        var sqlins2 = timeNow_toSQL
                    + data_quantity_adress_1
                    + data_quantity_adress_2
                    + data_quantity_adress_3
                    + data_quantity_adress_4
                    + data_quantity_adress_5
                    + data_quantity_adress_6
                    ;
        var sqlins = sqlins1 + sqlins2 + ");";
        // Thực hiện ghi dữ liệu vào SQL
        sqlcon.query(sqlins, function (err, result) {
            if (err) {
                console.log(err);
             } else {
                console.log("SQL - Ghi dữ liệu thành công");
              }
            });
    }
    sqlins_done = trigger;
}

// Đọc thị dữ liệu Cảnh báo
io.on("connection", function(socket){
    socket.on("msg_Alarm_Show", function(data)
    {
        var sqltable_Name = "alarm";
        var query = "SELECT * FROM " + sqltable_Name + " WHERE Status = 'I';";
        sqlcon.query(query, function(err, results, fields) {
            if (err) {
                console.log(err);
            } else {
                const objectifyRawPacket = row => ({...row});
                const convertedResponse = results.map(objectifyRawPacket);
                socket.emit('Alarm_Show', convertedResponse);
            }
        });
    });
});
