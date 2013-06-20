/* author: makto
 * data: 2013-6-6
 * 
 * JS code for FileHub
 */
function valid_dir(dirname){
    var name = $.trim(dirname);
    if ((!name) | (name.indexOf("/") != -1)){
        return false;
    } else {
        return true;
    }
}

function refresh_list(path){
    $.get("/files/", {"path":path},
          function(resp){
              $("#pathnow").text(path);
              $("#filelist").html(resp);
              var pathup = path.split('/').slice(0,-1).join('/');
              $("#pathup").text(pathup);
              if (path == '/'){
                  $("#updir").addClass("pure-button-disabled");
              } else if (!pathup) {
                  $("#pathup").text('/');
                  $("#updir").removeClass("pure-button-disabled");
              } else {
                  $("#updir").removeClass("pure-button-disabled");
              }
          });
}

// upload plugin related funtions
// begin
function uploadadd(e, data){
    // refresh upload files list
    var files = "";
    $.each(data.files, function(i, f){
        files = files + "<li>" + f.name + "</li>";
    });
    var text = $(files);
    $("#uploadlist ol").append(text);
    // activate upload button
    $("#upload").removeClass("pure-button-disabled");
    // add clear all button
    if (!$("#uploadlist a").text()){
        $('<a href="#">清除选择</a>').appendTo($("#uploadlist"))
            .click(function(e){
                e.preventDefault();
                $("#upload").off("click").addClass("pure-button-disabled");
                $("#uploadlist li").remove();
                $(this).remove();});
    }
    // bind upload action with button click
    data.context = [$("#upload").one("click", function(){
                            text.append('<span> .......上传中...</span>');
                            data.submit();}),
                    text];
}

function uploaddone(e, data){
    data.context[1].find("span").text(" .......上传成功！");
    window.setTimeout(function(){data.context[1].fadeOut(1500);}, 2000);
    window.setTimeout(function(){data.context[1].remove();}, 3501);
    // with .one method, the following code is unnecessary
    //data.context[0].off('click');
}

function uploadstart(e){
    $("#progressbar").progressbar();
    $("#dropzone").addClass("ui-helper-hidden");
    $("#upload").addClass("pure-button-disabled");
    $("#uploadlist a").remove();
}

function uploadstop(e){
    refresh_list($("#pathnow").text());
    window.setTimeout(function(){
        $("#progressbar").progressbar("destroy");
        $("#dropzone").removeClass("ui-helper-hidden");}, 1000);
}

function uploadprogress(e, data){
    var progress = parseInt(data.loaded / data.total * 100, 10);
    $("#progressbar").progressbar("value", progress);
}
// upload related funtions
// stop


$(document).ready(function(){

    refresh_list("/");

    // init upload plugin
    $("#fileupload").fileupload({
        //url: "/upload/",
        dataType: "text",
        autoUpload: false,
        dropZone: $("#dropzone"),
        replaceFileInput: false,
        formData: function(){
            return [{name: 'path', value: $("#pathnow").text()},
                    {name: 'type', value: 'file'}];},
        add: uploadadd,
        done: uploaddone,
        start: uploadstart,
        stop: uploadstop,
        progressInterval: 10,
        progressall: uploadprogress,
    });

    // init mkdir dialog
    $("#dirdialog").dialog({
        autoOpen: false,
        closeOnEscape: true,
        modal: true,
        show: "fade",
        hide: "fade",
        buttons: {
            "创建": function(){
                var dir = $("#newdir").val();
                if (!valid_dir(dir)){
                    $("#formaterror").removeClass("ui-helper-hidden");
                    return;
                } else {
                    $("#formaterror").addClass("ui-helper-hidden");
                    var path = $("#pathnow").text()
                    $.post("/files/",
                        {"type":"dir", "name":dir, "path":path},
                        function(resp){
                            if (resp == "ok"){
                                $("#posterror").addClass("ui-helper-hidden");
                                refresh_list(path);
                                $("#dirdialog").dialog("close");
                            } else {
                                $("#posterror").text(resp).removeClass("ui-helper-hidden");}});}},
        },
        close: function(e, u){
            $("#newdir").val("");
            $("#posterror").addClass("ui-helper-hidden");
            $("#formaterror").addClass("ui-helper-hidden");
        }
    });

    // init login dialog
    $("#logindialog").dialog({
        autoOpen: false,
        closeOnEscape: true,
        modal: true,
        show: "fade",
        hide: "fade",
        buttons: {
            "确定": function(){
                var uname = $("#uname").val();
                var upass = $("#upass").val();
                $.post("/user/", {"uname": uname, "upass": upass},
                    function(resp){
                        if(resp == "ok"){
                            location.reload();
                        } else {
                            $("#posterror2").text(resp).removeClass("ui-helper-hidden");
                        }
                    });
            },
        },
        close: function(e, u){
            $("#posterror2").addClass("ui-helper-hidden");
            $("#uname").val("");
            $("#upass").val("");
        }
    });

    // click events
    // begin
    $("#mkdir").click(function(){
        $("#dirdialog").dialog("open");
    });

    $("#updir").click(function(){
        var pathup = $("#pathup").text();
        if (!pathup) {
            return;
        }
        refresh_list(pathup);
    });

    $("#filelist").on("click", 'a.dir', function(e){
        e.preventDefault();
        var pathnow = $("#pathnow").text();
        var tmp;
        if (pathnow == '/'){tmp = '';}else{tmp='/'}
        var pathto = pathnow + tmp + $(this).text();
        refresh_list(pathto);
    });

    $("#filelist").on("click", "a.del", function(e){
        e.preventDefault();
        if($(this).parent().prev().find("a").attr("class") == "dir"){
            var yes = confirm("确定删掉这个目录下的所有文件吗？");
            if(!yes){return;}
        }
        var parenttr = $(this).parent().parent();
        $.ajax({
            url: "/files/?"+$.param({fid: parenttr.attr("id")}),
            type: "DELETE",
            //data: {fid: parenttr.attr("id")},
            dataType: "text",
            success: function(data, ts){
                if(data=="ok"){
                    parenttr.hide('slow',function(){$(this).remove();});
                }}});
    });
    
    $("#uinfo").on("click", "a#login", function(e){
        e.preventDefault();
        $("#logindialog").dialog("open");
    });

    $("#uinfo").on("click", "a#logout", function(e){
        e.preventDefault();
        $.ajax({url: "/user/", type: "DELETE", dataType: "text",
                success: function(data, ts){
                    if (data == "ok")location.reload();
                }});
    });
    // click events
    // stop

});


/* dropzone effects
 * begin */
$(document).on('drop dragover', function (e) {
        e.preventDefault();
});

$(document).on('dragover', function (e) {
    var dropZone = $("#dropzone");
    var found = false,
      	node = e.target;
    do {
        if (node === dropZone[0]) {
       		found = true;
       		break;
       	}
       	node = node.parentNode;
    } while (node != null);
    if (found) {
        dropZone.addClass('hover');
    } else {
        dropZone.removeClass('hover');
    }
});

$(document).on("drop", function (e) {
    var dropZone = $("#dropzone");
    var found = false,
      	node = e.target;
    do {
        if (node === dropZone[0]) {
       		found = true;
       		break;
       	}
       	node = node.parentNode;
    } while (node != null);
    if (found) {
        dropZone.removeClass("hover");
    }
});
/* dropzone effects
 * stop */
