# google_maps_scraper
Scrape marker info from embedded google maps.

requires selenium 2.53.6 and PyVirtualDisplay 0.2.1 (in order to run headless).

uses https://github.com/inaz2/proxy2

1. run setup_https_intercept.sh.
2. sudo apt-get install xvfb.
3. et voila.

tested with chrome. should work with firefox 30 but does not work with phantomjs.

#how does it work

create global vars 

```javascript
window.maxs_markers=[];
window.maxs_markers_latlng=[];
window.maxs_markers_infowindow=[];
```

and change the google maps marker constructor to store the markers when they're instantiated:

```javascript

_.ue = function(a) {
    if("position" in a){
        window.maxs_markers_latlng.push([a.position.lat(),a.position.lng()])
    }
    this.__gm = {
        set: null ,
        me: null
    };
    qe.call(this, a)
    window.maxs_markers.push(this)
}
```

this isn't enough though because you can't serialize the markers (and they don't have the infowindow content anyway): for example

```javascript
  google.maps.event.addListener(marker, 'click', function () {
      infowindow.setContent(html);
      infowindow.open(map, marker);
  });
```      

so change the setter for the infowindow

```javascript
_.k.set = function(a, b) {
    if(a=="content" && "anchor" in this){
        window.maxs_markers_infowindow.push([this.anchor.position.toString(),b])
    };
    if(a=="anchor" && "content" in this){
        window.maxs_markers_infowindow.push([b.position.toString(),this.content])
    };
    var c = Db(this);
    a += "";
    var d = jb(c, a);
    if (d)
        if (a = d.rb,
        d = d.Kc,
        c = "set" + _.Cb(a),
        d[c])
            d[c](b);
        else
            d.set(a, b);
    else
        this[a] = b,
        c[a] = null ,
        Ab(this, a)
};
```

and click all of the markers (since you store refs to them you can)

```javascript
for (var i = 0; i<window.maxs_markers.length;i++) {
    google.maps.event.trigger(window.maxs_markers[i],'click')
}
```

now just inject source into maps.google.com/maps/api/js whenever it's loaded by the page you want to scrape (hence the proxy).

# faq

1. **how did you find the constructor and setter**? the constructor is easy because the it's part of the api, so in maps.google.com/maps/api/js there's an assignment `Marker:_.ue`. to find the setter i used a debugger.
2. **why regex instead of serving a static local file?**
google re-obfuscates each time it releases a new version so the identifiers change.
3. **why serve over ssl?** all sorts of hsts non-sense.
