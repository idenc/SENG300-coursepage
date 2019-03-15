/**
 * Authentication component
 */

// Define attributes
const attribute = [
    {   
        "name"  : "graphic",
        "value" : false,
    },
]
const session = "session";

function initAuthTag(tag, attr){
    // Defind the object
    var Auth = Object.create(HTMLElement.prototype);

    // Initialize attributes
    attr.forEach(function(a){
        Object.defineProperty(Auth, attr.name, {value: a.value});
    });

    // Register Auth-tag's definition.
    customElements.define(tag, Auth);

    // Instantiate an auth-tag.
    document.createElement(tag);

    // Find all the tags occurrences (instances)
    var tagInstances = document.getElementsByTagName(tag);

    // For each tag's instance
    for ( var element in tagInstances ) {
        if (element.attributes.graphic && element.attributes.graphic.value == "true") {
            console.log("True");
        }
    };
}

initAuthTag('auth-tag', attribute);


