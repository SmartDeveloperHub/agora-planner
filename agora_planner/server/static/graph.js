/**
 * Created by fserena on 3/06/15.
 */

$(function () { // on dom ready

    var cy = cytoscape({
        container: document.getElementById('cy'),

        style: cytoscape.stylesheet()
            .selector('node')
            .css({
                'content': 'data(label)',
                'color': '#343435',
                'shape': 'data(shape)',
                'width': 'mapData(width, 1, 200, 1, 200)',
                'height': '40',
                'text-valign': 'center',
                'background-color': 'white',
                'font-weight': 'regular',
                'visibility': 'hidden'
            })
            .selector('edge')
            .css({
                'target-arrow-shape': 'triangle',
                'width': 3,
                'line-color': '#343435',
                'target-arrow-color': '#343435',
                'content': 'data(label)',
                'color': 'white',
                'edge-text-rotation': 'autorotate',
                'text-valign': 'top',
                'text-wrap': 'wrap',
                'text-background-color': '#343435',
                'text-background-shape': 'roundrectangle',
                'curve-style': 'bezier',
                'visibility': 'hidden'
            }).selector('node.highlighted')
            .css({
                //'background-color': '#037',
                'transition-property': 'background-color, line-color, target-arrow-color, color, border-width, shadow-color, visibility',
                'transition-duration': '0.5s',
                'color': '#343435',
                'border-width': 3,
                'border-opacity': 0.7,
                'font-weight': 'regular',
                'shadow-color': '#101010',
                'shadow-opacity': 0.5,
                'shadow-offset-x': 4,
                'shadow-offset-y': 3,
                'shadow-blur': 2,
                'visibility': 'visible'
            }).selector('edge.highlighted')
            .css({
                'transition-property': 'visibility',
                'transition-duration': '0.5s',
                'visibility': 'visible'
            }).selector('node.seed')
            .css({
                'border-color': '#0085ca',
                'shadow-color': '#0085ca'
            }).selector('edge.end')
            .css({
                'line-color': '#2a2',
                'target-arrow-color': '#292',
                'text-background-color': '#292'
            }).selector('node.end')
            .css({
                'border-color': '#2a2',
                'shadow-color': '#2a2'
            }),

        elements: {
            nodes: vGraph.nodes,
            edges: vGraph.edges
        }
    });

    var options = {
        name: 'arbor',

        animate: true, // whether to show the layout as it's running
        maxSimulationTime: 4000, // max length in ms to run the layout
        fit: false, // on every layout reposition of nodes, fit the viewport
        padding: 30, // padding around the simulation
        boundingBox: undefined, //{x1: 0, y1: 0, w: 1000, h: 1000}, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        ungrabifyWhileSimulating: false, // so you can't drag nodes during layout

        // callbacks on layout events
        ready: undefined, // callback on layoutready
        stop: undefined, // callback on layoutstop

        // forces used by arbor (use arbor default on undefined)
        repulsion: 2000,
        stiffness: undefined,
        friction: 0.9,
        gravity: true,
        fps: undefined,
        precision: 0.9,

        // static numbers or functions that dynamically return what these
        // values should be for each element
        // e.g. nodeMass: function(n){ return n.data('weight') }
        nodeMass: undefined,
        edgeLength: undefined,

        stepSize: 0.2, // smoothing of arbor bounding box

        // function that returns true if the system is stable to indicate
        // that the layout can be stopped
        stableEnergy: function (energy) {
            var e = energy;
            return (e.max <= 0.5) || (e.mean <= 0.3);
        },

        // infinite layout options
        infinite: true // overrides all other options for a forces-all-the-time mode
    };

    cy.layout(options);

    cy.bfs = [];

    vGraph.roots.forEach(function (r, index) {
        cy.bfs.push(
            {
                index: index,
                successors: cy.nodes().successors(),
                bfs: cy.elements().bfs('#' + vGraph.roots[index], function () {
                }, true)
            }
        );
    });

    var highlightNextEle = function (b) {
        b.successors[b.index].addClass('highlighted');
        //b.bfs.path[b.index].addClass('highlighted');
        console.log(b.successors);
        if (b.index < b.successors.length) {
            b.index++;
            setTimeout(function () {
                highlightNextEle(b);
            }, 200);
        }
    };

    // kick off first highlights
    cy.bfs.forEach(function (b) {
        highlightNextEle(b);
    });


}); // on dom ready

$(document).ready(function() {
    tps.forEach(function (tp) {
        $("#tps").append('<p>' + tp + ' .</p>')
    });
});
