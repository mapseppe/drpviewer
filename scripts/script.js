// The map
const map = L.map('map').setView([52.0, 5.0], 7);

// Basemap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Filter bad geometries
const validFeatures = geojsonData.features.filter(f => {
  return f.geometry &&
         f.geometry.type === "Point" &&
         Array.isArray(f.geometry.coordinates) &&
         f.geometry.coordinates.length === 2 &&
         typeof f.geometry.coordinates[0] === 'number' &&
         typeof f.geometry.coordinates[1] === 'number';
});

// Map good geometries
L.geoJSON({ type: "FeatureCollection", features: validFeatures }, {
  pointToLayer: function (feature, latlng) {
    return L.circleMarker(latlng, {
      radius: 6,
      fillColor: 'blue',
      color: '#000',
      weight: 1,
      fillOpacity: 0.8
    });
  },

  onEachFeature: function (feature, layer) {
    if (feature.properties && feature.properties.Full_Path && feature.properties.File_Name) {
      // Popup
      layer.bindPopup(feature.properties.File_Name);

      // Load image when clicking
      layer.on('click', () => {
        let fullPath = feature.properties.Full_Path || feature.properties.File_Name;
        if (!fullPath) return;

        // Convert backslashes to forward
        fullPath = fullPath.replace(/\\/g, '/');

        // Get path
        const drpimagesIndex = fullPath.toLowerCase().indexOf('drpimages/');
        let relativePath = '';

        if (drpimagesIndex !== -1) {
          relativePath = fullPath.substring(drpimagesIndex);
        } else {
          const parts = fullPath.split('/');
          relativePath = parts.slice(-3).join('/');
          relativePath = 'drpimages/' + relativePath;
        }

        const img = document.getElementById('feature-image');
        if (img) {
          img.src = '';
          img.src = relativePath + '?t=' + new Date().getTime();
        }
      });
    }
  }
}).addTo(map);
