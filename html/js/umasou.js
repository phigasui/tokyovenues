function initialize(){
    page = 0;
    requesting = true;
    radius = 3.0;
    lat = 36;
    lon = 140;
}

function listClear(){
    $('#imgs ul').remove();
    $('#imgs').append('<ul></ul>');
}

function getLocation(){
    listClear();
    initialize();
    navigator.geolocation.getCurrentPosition(successFunc, errorFunc);
}

function getLocationFromAddress(){
    listClear();
    initialize();
    $.ajax({
        url: 'https://maps.googleapis.com/maps/api/geocode/json?sensor=true'
            + '&address=' + $('#address').val(),
        type: 'GET',
        dataType: 'JSON',
        async: false,
        success: function(data){
            var results = data['results'];
            if(results.length > 0){
                loc = results[0]['geometry']['location'];
                lat = loc['lat'];
                lon = loc['lng'];
            }
        }
    });
    getItems(page);
}

function successFunc(position){
    requesting = false;
    lat = position.coords.latitude;
    lon = position.coords.longitude;
    getItems(page);
}

function errorFunc(error){
    alert("ブラウザの位置情報を許可してください");
}

function getItems(page){
    var offset = page * 20;
    console.log('items?lat=' + lat + '&lon=' + lon
                + '&offset=' + offset + '&radius=' + radius);
    $.ajax({
        url: 'items?lat=' + lat + '&lon=' + lon
            + '&offset=' + offset + '&radius=' + radius,
        type: 'GET',
        dataType: 'JSON',
        async: false,
        success: function(data){
            var items = data['items'];

            if(items.length == 0 && page == 0){
                $("div#imgs ul").text("この周辺には記事がありません(>_<;)");
            }

            for(i in items){
                if(items[i]['img_url']==null) continue;
                $("div#imgs ul").append('<li><p class="trimming">'
                                        + '<a target ="_brank"'
                                        + 'href="' + items[i]['url']
                                        + '"><img src="' + items[i]['img_url']
                                        + '"></a></p></li>');
            }
        }
    });
    $("div#imgs ul li").fadeIn(1000);
    requesting = false;
}

var page = 0;
var requesting = true;
var lat = 36;
var lon = 140;
var radius = 1.5;

window.onload = initialize;

$(window).bind("scroll", function(){
    scrollHeight = $(document).height();
    scrollPostion = $(window).height() + $(window).scrollTop();
    if((scrollHeight - scrollPostion) / scrollHeight <=0.1){
        if(!requesting){
            page = page + 1;
            requesting = true;
            getItems(page);
        }
    }
});

$(function() {
    $(window).scroll(function() {
        if($(window).scrollTop() >= 350) {
            $("#to_top").fadeIn();
        }
        else {
            $("#to_top").fadeOut();
        }}
                    );

    $("#to_top a").click(function(){
        $("html, body").animate({scrollTop: 0});
        return false;
    });
});
