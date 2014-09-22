from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from annoying.functions import get_object_or_None
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse, \
                        HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from ratelimit.decorators import ratelimit
from .models import Election, Candidate, VoteCode, ElectionVoteCode, Vote, \
                    Preference, AuditEntry
from .forms import GenerateVoteCodesForm


class ElectionList(ListView):
    model = Election


class CandidateList(ListView):
    model = Candidate


class AuditEntryList(ListView):
    model = AuditEntry


class AuditEntryDetail(DetailView):
    model = AuditEntry


class AuditEntryRawDetail(DetailView):
    model = AuditEntry
    content_type = 'text/plain'
    template_name = 'vote3fe/auditentry_detail_raw.txt'


# the way this returns data to the user is to return the first and last
# id's of the voting codes. This could potentially go awry if multiple requests
# are being executed simultaneously. We /may/ be able to get around this by
# wrapping it all in a transaction, but I think the odds of hitting this in
# practise are essentially nil so I've left it for now.
@user_passes_test(lambda u: u.is_superuser)
def generate_vote_codes(request):
    if request.method == 'POST':
        form = GenerateVoteCodesForm(request.POST)
        if form.is_valid():
            # generate the voting codes, yay!
            count = form.cleaned_data['count']
            elections = form.cleaned_data['elections']
            votecodes = []
            for i in range(0, count):
                votecode = VoteCode.objects.create()
                votecodes += [votecode]
                for e in elections:
                    evc = ElectionVoteCode(election=e, vote_code=votecode)
                    evc.save()
            return HttpResponseRedirect(reverse('vote3fe:vote_codes',
                                                args=(votecodes[0].id,
                                                      votecodes[-1].id)))

    else:
        form = GenerateVoteCodesForm()

    return render(request, 'vote3fe/generate_vote_codes.html', {'form': form})


# we only use this to get the codes we've just generated, so it only takes
# the vote_codes/from/to/ form.
class VoteCodesList(ListView):

    def get_queryset(self):
        return VoteCode.objects.filter(id__gte=self.args[0],
                                       id__lte=self.args[1])    

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(VoteCodesList, self).dispatch(*args, **kwargs)


# start using a votecode
# we display the list of elections that are available and unused.
#
# this function also has to be ratelimited to stop guessing them.
# method=None -> all methods count towards rate limit.
@ratelimit(block=True, method=None)
def vote_code(request, votecode_param):    
    votecode = get_object_or_404(VoteCode, vote_code=votecode_param)

    elections = votecode.elections.filter(electionvotecode__used=False)

    return render(request, 'vote3fe/vote_code.html',
                  {'elections': elections, 'votecode': votecode_param})


# there's probably a better, more idiomatic way to do this. Oh well.
@transaction.atomic
def vote(request, votecode_param, election):

    votecode = get_object_or_404(VoteCode, vote_code=votecode_param)
    election = get_object_or_404(Election, id=election)

    # verify that the election is allowed:
    if not election in votecode.elections.filter(electionvotecode__used=False):
        return HttpResponseForbidden('This is not an unused voting code for this election.')

    # verify that the election is open:
    if not election.isOpen:
        return HttpResponseForbidden('This election is closed for voting.')
    
    if request.method == 'GET':
        # get the candidates in ballot order:
        candidates = election.candidates.order_by('ballotentry__position')
        return render(request, 'vote3fe/vote.html',
                      {'election': election, 'candidates': candidates,
                       'votecode_param': votecode_param})

    elif request.method == 'POST':
        # mark the votecode as used, preventing multiple submissions
        # running concurrently
        evc = votecode.electionvotecode_set.get(election=election)
        evc.used = True
        evc.save()
        vote = Vote.objects.create(election=election)
        # verify the data and add it to the vote
        # anything invalid - just ignore it. You only get one shot at this.
        for x in request.POST:
            if x == 'csrfmiddlewaretoken':
                continue

            parts = x.split('-')
            if len(parts) != 2 or parts[0] != 'candidate':
                continue

            candidate = get_object_or_None(Candidate, id=parts[1])
            try:
                preference = int(request.POST[x])
            except ValueError:
                preference = None

            try:
                pref = Preference(vote=vote, candidate=candidate,
                                  preference=preference)
                pref.save()
            except Exception:
                pass

        # create an audit trail entry
        entry = render_to_string('vote3fe/audit/vote.txt',
                                 { 'post': request.POST,
                                   'vote': vote,
                                   'strict_secrecy': \
                                     settings.VOTE3_STRICT_SECRECY,
                                   'vote_code': votecode_param,
                                   'hash': AuditEntry.next_hash(),
                                 })
        a = AuditEntry.objects.create(entry=entry)

    return HttpResponseRedirect(reverse('vote3fe:audit_entry',
                                        kwargs={'pk': a.pk}))


def audit_entry_count(request, raw=False):
    entry = render_to_string('vote3fe/audit/count.txt',
                             { 'count': AuditEntry.objects.count(),
                               'hash': AuditEntry.next_hash() })

    signedentry = AuditEntry.sign(entry)

    if raw:
        return HttpResponse(signedentry, content_type = 'text/plain')

    else:
        return render(request,
                      'vote3fe/auditentry_detail.html',
                      { 'object': {'entry': signedentry}})
