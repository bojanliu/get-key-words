//显示灰色JS遮罩层
function showBg(ct,content){
var bH=$("body").height();
var bW=$("body").width()+16;
var objWH=getObjWh(ct);
$("#fullbg").css({width:bW,height:bH,display:"block"});
var tbT=objWH.split("|")[0]+"px";
var tbL=objWH.split("|")[1]+"px";
$("#"+ct).css({top:tbT,left:tbL,display:"block"});
$("#"+content).html("<div style='text-align:center;font-size:14px;'>正在处理中，请稍后...</div>");
$(window).scroll(function(){resetBg()});
$(window).resize(function(){resetBg()});
}
function getObjWh(obj){
var st=document.documentElement.scrollTop;//滚动条距顶部的距离
var sl=document.documentElement.scrollLeft;//滚动条距左边的距离
var ch=document.documentElement.clientHeight;//屏幕的高度
var cw=document.documentElement.clientWidth;//屏幕的宽度
var objH=$("#"+obj).height();//浮动对象的高度
var objW=$("#"+obj).width();//浮动对象的宽度
var objT=Number(st)+(Number(ch)-Number(objH))/2;
var objL=Number(sl)+(Number(cw)-Number(objW))/2;
return objT+"|"+objL;
}
function resetBg(){
var fullbg=$("#fullbg").css("display");
if(fullbg=="block"){
var bH2=$("body").height();
var bW2=$("body").width()+16;
$("#fullbg").css({width:bW2,height:bH2});
var objV=getObjWh("dialog");
var tbT=objV.split("|")[0]+"px";
var tbL=objV.split("|")[1]+"px";
$("#dialog").css({top:tbT,left:tbL});
}
}

//关闭灰色JS遮罩层和操作窗口
function closeBg(){
$("#fullbg").css("display","none");
$("#dialog").css("display","none");
}