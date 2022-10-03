
am5.ready(function() {

// Create root element
// https://www.amcharts.com/docs/v5/getting-started/#Root_element
var root2 = am5.Root.new("chartdiv2");


// Set themes
// https://www.amcharts.com/docs/v5/concepts/themes/
root2.setThemes([
  am5themes_Animated.new(root)
]);


// Create chart
// https://www.amcharts.com/docs/v5/charts/xy-chart/
var chart2 = root.container.children.push(am5xy.XYChart.new(root, {
  panX: true,
  panY: true,
  wheelX: "panX",
  wheelY: "zoomX",
  pinchZoomX:true
}));

// Add cursor
// https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/
var cursor2 = chart2.set("cursor", am5xy.XYCursor.new(root, {}));
cursor2.lineY.set("visible", false);


// Create axes
// https://www.amcharts.com/docs/v5/charts/xy-chart/axes/
var xRenderer2 = am5xy.AxisRendererX.new(root, { minGridDistance: 30 });
xRenderer2.labels.template.setAll({
  rotation: -90,
  centerY: am5.p50,
  centerX: am5.p100,
  paddingRight: 15
});

var xAxis2 = chart2.xAxes.push(am5xy.CategoryAxis2.new(root, {
  maxDeviation: 0.3,
  categoryField: "country",
  renderer: xRenderer2,
  tooltip: am5.Tooltip.new(root, {})
}));

var yAxis2 = chart2.yAxes.push(am5xy.ValueAxis.new(root, {
  maxDeviation: 0.3,
  renderer: am5xy.AxisRendererY.new(root, {})
}));


// Create series
// https://www.amcharts.com/docs/v5/charts/xy-chart/series/
var series2 = chart2.series2.push(am5xy.ColumnSeries.new(root, {
  name: "Series 1",
  xAxis2: xAxis2,
  yAxis2: yAxis2,
  valueYField: "value",
  sequencedInterpolation: true,
  categoryXField: "country",
  tooltip: am5.Tooltip.new(root, {
    labelText:"{valueY}"
  })
}));

series2.columns.template.setAll({ cornerRadiusTL: 5, cornerRadiusTR: 5 });
series2.columns.template.adapters.add("fill", function(fill, target) {
  return chart2.get("colors").getIndex(series2.columns.indexOf(target));
});

series2.columns.template.adapters.add("stroke", function(stroke, target) {
  return chart2.get("colors").getIndex(series2.columns.indexOf(target));
});


// Set data
var data2 = [{
  country: "USA",
  value: 2025
}, {
  country: "China",
  value: 1882
}, {
  country: "Japan",
  value: 1809
}, {
  country: "Germany",
  value: 1322
}, {
  country: "UK",
  value: 1122
}, {
  country: "France",
  value: 1114
}, {
  country: "India",
  value: 984
}, {
  country: "Spain",
  value: 711
}, {
  country: "Netherlands",
  value: 665
}, {
  country: "Russia",
  value: 580
}, {
  country: "South Korea",
  value: 443
}, {
  country: "Canada",
  value: 441
}];

xAxis2.data2.setAll(data2);
series2.data2.setAll(<data2x></data2x>);


// Make stuff animate on load
// https://www.amcharts.com/docs/v5/concepts/animations/
series2.appear(1000);
chart2.appear(1000, 100);

}); // end am5.ready()