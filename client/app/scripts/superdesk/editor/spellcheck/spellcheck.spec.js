
'use strict';

describe('spellcheck', function() {
    var DICT = {
            what: 1,
            foo: 1,
            bar: 1,
            f1: 1,
            '3d': 1,
            is: 1,
            and: 1
        },
        TEXT = 'wha is foo, f1, 4k and 3d?';

    beforeEach(module('superdesk.editor.spellcheck'));
    beforeEach(inject(function(dictionaries, $q) {
        spyOn(dictionaries, 'fetch').and.returnValue($q.when({_items: [{}]}));
        spyOn(dictionaries, 'open').and.returnValue($q.when({_id: 'foo', content: DICT}));
    }));

    it('can find errors in given text', inject(function(spellcheck, $rootScope) {
        var errors;
        spellcheck.errors(TEXT).then(function(_errors) {
            errors = _errors;
        });

        $rootScope.$digest();
        expect(errors).toEqual(['wha', '4k']);
    }));

    it('can render errors in given node', inject(function(spellcheck, $rootScope) {
        var p = document.createElement('p');
        p.contentEditable = 'true';
        p.appendChild(document.createTextNode(TEXT));
        document.body.appendChild(p);

        spellcheck.render(p);
        $rootScope.$digest();

        expect(p.innerHTML)
            .toBe('<span class="sderror">wha</span> is foo, f1, <span class="sderror">4k</span> and 3d?');

        expect(spellcheck.clean(p)).toBe(TEXT);
    }));
});
